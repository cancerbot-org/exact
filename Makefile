pytest:
	pytest

migrate:
	GDAL_LIBRARY_PATH=/opt/homebrew/lib/libgdal.dylib GEOS_LIBRARY_PATH=/opt/homebrew/lib/libgeos_c.dylib python manage.py migrate

migrations:
	GDAL_LIBRARY_PATH=/opt/homebrew/lib/libgdal.dylib GEOS_LIBRARY_PATH=/opt/homebrew/lib/libgeos_c.dylib python manage.py makemigrations

shell:
	python manage.py shell

runserver:
	python manage.py runserver

createsuperuser:
	python manage.py createsuperuser

seed:
	python manage.py seed_reference_data
