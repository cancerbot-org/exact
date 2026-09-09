"""HTTP surface added/repaired in phase 0 of the federated Find Trials plan.

Four things the federated remote needs and could not get before:

  * `POST /trials/search/match/` — the `search` action reachable with an
    inline `patient_info` body, so sorting and the tab counts work for a
    caller that cannot send a GET body.
  * `tabCounts` on the search response — per-tab totals without a second
    round trip, taken over the queryset the same response lists.
  * `?type=favorites` / `?type=my_trials` — rejected with 400 instead of
    raising FieldError (500) or silently returning the whole corpus.
  * `?phase=` — actually filters.

See docs/federated-ui-parity-plan.md.
"""
from datetime import date

import pytest
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from accounts.models import Identity
from tests.factories import TrialFactory


@pytest.fixture
def authed_client(db):
    user, _ = Identity.objects.get_or_create(issuer='urn:local', sub='phase0-tester')
    token, _ = Token.objects.get_or_create(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    return client


MM = {'patient_info': {'disease': 'multiple myeloma'}}


def potential_trial(**kwargs):
    """A trial the reference patient cannot be judged against yet.

    `ecog_performance_status_max` is a requirement the MM payload above says
    nothing about, so the matcher counts one unfilled attribute and the trial
    lands in `potential` rather than `eligible`.
    """
    return TrialFactory(disease='Multiple Myeloma', ecog_performance_status_max=2, **kwargs)


@pytest.mark.django_db
class TestSearchMatchPost:
    def test_unauthenticated_post_returns_401(self):
        assert APIClient().post('/trials/search/match/', {}, format='json').status_code == 401

    def test_returns_the_paginated_search_shape(self, authed_client):
        TrialFactory(disease='Multiple Myeloma')
        response = authed_client.post('/trials/search/match/', MM, format='json')
        assert response.status_code == 200
        assert 'results' in response.data
        assert 'itemsTotalCount' in response.data

    def test_inline_patient_info_scopes_to_disease(self, authed_client):
        """The body has to reach the matcher, exactly as it does for `match`.

        Strict equality rather than membership: a regression that widened the
        response to the disease-agnostic union would still contain the MM
        trial and would pass a membership check.
        """
        mm = TrialFactory(disease='Multiple Myeloma')
        TrialFactory(disease='Breast Cancer')
        response = authed_client.post('/trials/search/match/', MM, format='json')
        assert {t['trialId'] for t in response.data['results']} == {mm.id}

    def test_sort_is_honoured(self, authed_client):
        """The reason this alias exists.

        `POST /trials/match/` binds to `list`, whose ordering is fixed at
        `-match_score, -posted_date, id`, so `?sort=` did nothing for a
        caller on the inline path. Sorting by enrollment because it is a
        plain trial column: it does not depend on the matcher assigning
        distinguishable scores to the fixtures.
        """
        small = TrialFactory(disease='Multiple Myeloma', enrollment_count=10)
        large = TrialFactory(disease='Multiple Myeloma', enrollment_count=900)
        response = authed_client.post(
            '/trials/search/match/?sort=enrollment', MM, format='json',
        )
        assert response.status_code == 200
        ids = [t['trialId'] for t in response.data['results']]
        assert ids.index(large.id) < ids.index(small.id)

    def test_the_list_alias_does_not_sort_by_enrollment(self, authed_client):
        """Non-vacuity guard for the test above.

        If `search_match` ever silently rebound to `list`, the sort assertion
        could still pass whenever the fixtures happened to land in the right
        order. So assert the other half directly: `match` falls back to
        `-posted_date` once match scores tie, and these fixtures make that
        the opposite of enrollment order.

        The tie is asserted rather than assumed — it holds because these
        three trials differ only in fields the matcher does not read, and a
        future factory change could break that silently.
        """
        for day, enrollment in ((1, 300), (2, 200), (3, 100)):
            TrialFactory(
                disease='Multiple Myeloma',
                posted_date=date(2026, 1, day),
                enrollment_count=enrollment,
            )
        response = authed_client.post('/trials/match/?sort=enrollment', MM, format='json')
        assert response.status_code == 200
        results = response.data['results']
        scores = {t['matchScore'] for t in results}
        assert len(scores) == 1, (
            f'fixtures no longer tie on matchScore ({scores}); this test '
            'assumes the tie so that -posted_date decides the order'
        )
        posted = [t['postedDate'] for t in results]
        assert posted == sorted(posted, reverse=True), (
            f'{posted}: the list alias must fall back to -posted_date, not '
            'honour ?sort=enrollment'
        )


@pytest.mark.django_db
class TestTabCounts:
    """`tabCounts` on the search response, in place of a counts endpoint.

    A standalone `GET /trials/counts/` cannot work for the caller that needs
    it: counts are only meaningful under a patient context, the only way to
    send one is a POST body, and with `patient_info=None` the annotation
    collapses to `num_nonnulls(NULL)` — `potential` is then structurally 0
    and the "matched corpus" is the whole table. Riding on the search
    response also keeps counted and listed rows the same set by construction.
    """

    def test_present_on_the_search_response(self, authed_client):
        TrialFactory(disease='Multiple Myeloma')
        data = authed_client.post('/trials/search/match/', MM, format='json').data
        assert set(data['tabCounts']) == {'eligible', 'potential'}

    def test_partitions_the_matched_corpus(self, authed_client):
        """Non-vacuous: one fixture is genuinely potential, two eligible.

        Without the potential fixture this assertion reduces to `n + 0 == n`
        and cannot detect either overlap or loss.
        """
        TrialFactory(disease='Multiple Myeloma')
        TrialFactory(disease='Multiple Myeloma')
        potential_trial()
        data = authed_client.post('/trials/search/match/', MM, format='json').data
        assert data['tabCounts']['potential'] == 1, (
            'the potential fixture stopped being potential; the partition '
            'assertion below would be vacuous'
        )
        assert data['tabCounts']['eligible'] == 2
        assert (
            data['tabCounts']['eligible'] + data['tabCounts']['potential']
            == data['itemsTotalCount']
        )

    @pytest.mark.parametrize('search_type', ['eligible', 'potential'])
    def test_counts_describe_the_corpus_not_the_active_tab(
        self, authed_client, search_type,
    ):
        """The whole point of the counts.

        `with_potential_attrs_count` applies the `type` narrowing as well as
        the annotation, so counting the response's own queryset counted an
        already-narrowed set: on the Potential tab the Eligible badge read 0
        and the tab bar could not be labelled from the response it came with.
        """
        TrialFactory(disease='Multiple Myeloma')
        TrialFactory(disease='Multiple Myeloma')
        potential_trial()
        data = authed_client.post(
            f'/trials/search/match/?type={search_type}', MM, format='json',
        ).data
        assert data['tabCounts'] == {'eligible': 2, 'potential': 1}, (
            f'?type={search_type} narrowed the counts as well as the rows'
        )
        # ...while the listed rows ARE narrowed.
        assert data['itemsTotalCount'] == (2 if search_type == 'eligible' else 1)

    def test_counts_move_with_every_filter_the_list_obeys(self, authed_client):
        """Counted rows and listed rows must come from the same filtering.

        `?search=` is applied by DRF's SearchFilter in `filter_queryset`,
        *outside* `filtered_trials` — so a counts implementation that skipped
        it would promise rows the list cannot show. `?searchTitle=` goes
        through `filtered_trials` instead, so both routes are exercised.
        """
        TrialFactory(disease='Multiple Myeloma', brief_title='Daratumumab study')
        TrialFactory(disease='Multiple Myeloma', brief_title='Lenalidomide study')
        for query in ('search=Daratumumab', 'searchTitle=Daratumumab'):
            data = authed_client.post(
                f'/trials/search/match/?{query}', MM, format='json',
            ).data
            total = data['tabCounts']['eligible'] + data['tabCounts']['potential']
            assert total == data['itemsTotalCount'] == 1, (
                f'?{query}: counts {total} vs listed {data["itemsTotalCount"]}'
            )

    def test_omitted_without_patient_context(self, authed_client):
        """A count with no patient context asserts a verdict nobody made.

        With `patient_info=None` the annotation collapses to
        `num_nonnulls(NULL)`, so every row counts as eligible and nothing
        counts as potential — the corpus relabelled as a clinical result.
        This is the failure that killed the standalone counts endpoint, and
        `GET /trials/search/` is equally GET-only, so the key has to be
        absent rather than wrong.
        """
        TrialFactory(disease='Multiple Myeloma')
        TrialFactory(disease='Breast Cancer')
        data = authed_client.get('/trials/search/').data
        assert 'tabCounts' not in data
        # The rows themselves are still served — only the verdict is withheld.
        assert data['itemsTotalCount'] == 2

    def test_omitted_under_type_all(self, authed_client):
        """`type=all` takes the admin branch, which skips the eligibility
        filter — the rows are the corpus the caller asked for, but no
        per-row verdict was computed, so counting them as eligible would
        attach one retroactively."""
        TrialFactory(disease='Multiple Myeloma')
        data = authed_client.post('/trials/search/match/?type=all', MM, format='json').data
        assert 'tabCounts' not in data


@pytest.mark.django_db
class TestUserScopedSearchTypesRejected:
    """`favorites` / `my_trials` name per-user state EXACT does not hold."""

    @pytest.mark.parametrize('search_type', ['favorites', 'my_trials', 'not_eligible'])
    @pytest.mark.parametrize('path', ['/trials/', '/trials/search/', '/trials/count/'])
    def test_rejected_with_400(self, authed_client, search_type, path):
        TrialFactory(disease='Multiple Myeloma')
        response = authed_client.get(f'{path}?type={search_type}')
        assert response.status_code == 400, (
            f'{path}?type={search_type} returned {response.status_code}; '
            'favorites used to raise FieldError (500), my_trials returned the '
            'unfiltered corpus as if it were the patient list, and not_eligible '
            'returned the eligible + potential set — the inverse of its name'
        )
        assert 'type' in response.data

    @pytest.mark.parametrize('search_type', ['favorites', 'my_trials'])
    def test_rejected_on_the_post_aliases_too(self, authed_client, search_type):
        TrialFactory(disease='Multiple Myeloma')
        for path in ('/trials/match/', '/trials/search/match/'):
            response = authed_client.post(f'{path}?type={search_type}', MM, format='json')
            assert response.status_code == 400, f'{path} accepted {search_type}'

    @pytest.mark.parametrize('search_type', ['favorites', 'my_trials'])
    def test_the_detail_page_still_works_with_the_tab_in_the_query_string(
        self, authed_client, search_type,
    ):
        """Blast-radius guard.

        `retrieve` ignores `type` entirely, so a UI that carries the tab it
        came from across a list -> detail navigation must not get a 400 for
        a parameter the detail endpoint never reads.

        Exercised through the POST detail alias because that is the path the
        federated remote uses, and because plain `GET /trials/{id}/` without
        any patient context 500s for an unrelated, pre-existing reason (the
        matcher dereferences a None patient_info) — see #423.
        """
        trial = TrialFactory(disease='Multiple Myeloma')
        response = authed_client.post(
            f'/trials/{trial.id}/match/?type={search_type}', MM, format='json',
        )
        assert response.status_code == 200

    @pytest.mark.parametrize('search_type', ['eligible', 'potential', 'eligible_and_potential'])
    def test_supported_types_still_work(self, authed_client, search_type):
        TrialFactory(disease='Multiple Myeloma')
        response = authed_client.get(f'/trials/search/?type={search_type}')
        assert response.status_code == 200

    def test_all_is_deliberately_not_rejected(self, authed_client):
        """`all` reaches the same admin branch as `my_trials` and returns the
        same unnarrowed corpus — but that corpus is what it names, so it is
        left alone. Pinned so the asymmetry reads as a decision, not a gap."""
        TrialFactory(disease='Multiple Myeloma')
        assert authed_client.get('/trials/search/?type=all').status_code == 200


@pytest.mark.django_db
class TestPhaseFilter:
    """`?phase=` reached the dataclass field but never the query string.

    `by_phase` reads `PHASE_CODE_MAPPING.index(phase)` and keeps trials at
    that phase *or later*, so PHASE3 keeps III and IV and drops I and II.
    """

    def test_narrows_to_the_requested_phase_and_later(self, authed_client):
        early = TrialFactory(disease='Multiple Myeloma', phases=['PHASE1'], phase_code_min=1)
        late = TrialFactory(disease='Multiple Myeloma', phases=['PHASE3'], phase_code_min=3)
        response = authed_client.get('/trials/search/?phase=PHASE3')
        assert response.status_code == 200
        ids = {t['trialId'] for t in response.data['results']}
        assert late.id in ids
        assert early.id not in ids, (
            'a PHASE1 trial survived ?phase=PHASE3 — the parameter is being '
            'dropped before it reaches StudyPreferences again'
        )

    def test_absent_phase_keeps_everything(self, authed_client):
        TrialFactory(disease='Multiple Myeloma', phases=['PHASE1'], phase_code_min=1)
        TrialFactory(disease='Multiple Myeloma', phases=['PHASE3'], phase_code_min=3)
        response = authed_client.get('/trials/search/')
        assert len(response.data['results']) == 2

    def test_unknown_phase_value_is_ignored_not_fatal(self, authed_client):
        """`by_phase` only acts on values it recognises. A junk value must
        not 500 and must not silently empty the list."""
        TrialFactory(disease='Multiple Myeloma', phases=['PHASE2'], phase_code_min=2)
        response = authed_client.get('/trials/search/?phase=NOT_A_PHASE')
        assert response.status_code == 200
        assert len(response.data['results']) == 1

    def test_trials_without_a_phase_drop_out_of_every_phase_filter(self, authed_client):
        """Documents a sharp edge that activating this parameter exposes.

        `phase_code_min` is nullable and `NULL >= 0` is NULL, so a trial
        whose phase was never ingested disappears the moment the user
        touches the phase filter — including at the lowest value, where a
        reader would expect "everything". Worth knowing before the filter
        reaches the UI in phase 1; changing `by_phase` would be a matcher
        behaviour change and is out of scope here.
        """
        TrialFactory(disease='Multiple Myeloma', phases=[], phase_code_min=None)
        assert len(authed_client.get('/trials/search/').data['results']) == 1
        response = authed_client.get('/trials/search/?phase=EARLY_PHASE1')
        assert response.data['results'] == []


@pytest.mark.django_db
class TestRecruitmentStatusOptions:
    """`/form-settings/` gains the trial recruitment states.

    The only status enum it exposed was `statuses` — the patient-invitation
    one ("Looking for trial", "Waiting for patient acceptance") — so a client
    building a recruitment filter either rendered that wrong vocabulary or
    hard-coded the list, which the federated remote does today.
    """

    def test_options_are_exposed(self, authed_client):
        response = authed_client.get('/form-settings/')
        assert response.status_code == 200
        values = [o['value'] for o in response.data['recruitmentStatuses']['options']]
        # The two the queryset special-cases, plus the fall-through states.
        assert 'RECRUITING' in values
        assert 'RECRUITING_AND_NOT_YET_RECRUITING' in values
        assert 'TERMINATED' in values

    def test_every_offered_value_actually_selects_its_trials(self, authed_client):
        """A status-200 assertion would not bite here: `by_recruitment_status`
        never raises — an unrecognised value just matches zero rows, so a
        typo'd option would pass. Assert the option round-trips instead:
        seed one trial in that state and require the filter to return it.
        """
        options = authed_client.get('/form-settings/').data['recruitmentStatuses']['options']
        singles = [o['value'] for o in options
                   if o['value'] not in ('', 'RECRUITING_AND_NOT_YET_RECRUITING')]
        assert singles, 'no single-state options to check'
        for value in singles:
            trial = TrialFactory(disease='Multiple Myeloma', recruitment_status=value)
            response = authed_client.get(f'/trials/search/?recruitmentStatus={value}')
            assert response.status_code == 200
            assert trial.id in {t['trialId'] for t in response.data['results']}, (
                f'{value!r} is offered by /form-settings/ but selects nothing'
            )
            trial.delete()

    def test_the_combined_value_selects_both_of_its_states(self, authed_client):
        recruiting = TrialFactory(disease='Multiple Myeloma', recruitment_status='RECRUITING')
        not_yet = TrialFactory(disease='Multiple Myeloma', recruitment_status='NOT_YET_RECRUITING')
        completed = TrialFactory(disease='Multiple Myeloma', recruitment_status='COMPLETED')
        response = authed_client.get(
            '/trials/search/?recruitmentStatus=RECRUITING_AND_NOT_YET_RECRUITING'
        )
        ids = {t['trialId'] for t in response.data['results']}
        assert ids == {recruiting.id, not_yet.id}
        assert completed.id not in ids

    def test_does_not_retype_the_trial_detail_field(self, authed_client):
        """Guard on the namespace collision this key was renamed to avoid.

        `trial_details/trial_attributes.py` resolves a detail field's
        `options` by matching the field's name against `all_options()` keys.
        A key spelled `recruitmentStatus` (singular) therefore turns the
        detail page's Recruitment Status from a plain string into a select —
        an unrelated contract change riding along on a filter fix.
        """
        from trials.services.value_options import ValueOptions

        assert 'recruitmentStatuses' in ValueOptions().all_options()
        assert 'recruitmentStatus' not in ValueOptions().all_options()
