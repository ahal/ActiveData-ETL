
export PYTHONPATH=.

python testlog_etl/pulse_logger.py --settings=resources/settings/pulse_logger_beta_settings.json &
python testlog_etl/etl.py --settings=resources/settings/etl_beta_settings.json &
python testlog_etl/push_to_es.py --settings=resources/settings/push_to_es_beta_settings.json &
