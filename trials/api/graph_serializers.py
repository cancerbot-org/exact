from __future__ import annotations

from typing import Optional

from rest_framework import serializers

from trials.models import Trial


class GraphTrialNodeSerializer(serializers.ModelSerializer):
    nodeId = serializers.SerializerMethodField()
    trialId = serializers.IntegerField(source="id")
    studyId = serializers.CharField(source="study_id")
    studyUrl = serializers.SerializerMethodField()
    briefTitle = serializers.CharField(source="brief_title", allow_blank=True, allow_null=True)
    recruitmentStatus = serializers.CharField(source="recruitment_status", allow_blank=True, allow_null=True)
    sponsorName = serializers.CharField(source="sponsor_name", allow_blank=True, allow_null=True, required=False)
    goodnessScore = serializers.IntegerField(source="goodness_score", required=False, allow_null=True)
    matchScore = serializers.IntegerField(source="match_score", required=False, allow_null=True)
    link = serializers.CharField(allow_blank=True, allow_null=True, required=False)

    class Meta:
        model = Trial
        fields = (
            "nodeId",
            "trialId",
            "studyId",
            "studyUrl",
            "briefTitle",
            "recruitmentStatus",
            "sponsorName",
            "link",
            "goodnessScore",
            "matchScore",
        )

    def get_nodeId(self, obj: Trial) -> str:
        return f"trial:{obj.id}"

    def get_studyUrl(self, obj: Trial) -> Optional[str]:
        study_id = getattr(obj, "study_id", None)
        if not study_id:
            return None
        base_url = (self.context.get("base_url") or "").rstrip("/")
        path = f"/t/{study_id}"
        return f"{base_url}{path}" if base_url else path
