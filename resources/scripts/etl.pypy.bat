set PYTHONPATH=.
set PYPY_GC_MAX=3GB
pypy testlog_etl/etl.py --settings=resources\settings\etl_dev_2_staging_settings.json
