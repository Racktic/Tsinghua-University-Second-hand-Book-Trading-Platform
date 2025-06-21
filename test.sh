coverage run --source backend,apps -m pytest apps/accounts/tests.py apps/sales/test_need.py apps/chat/tests.py apps/sales/test_purchase.py apps/sales/tests.py apps/sales/test_schedule.py apps/sales/test_location.py apps/sales/test_send_system_notification.py --junit-xml=xunit-reports/xunit-result.xml
ret=$?
coverage xml -o coverage-reports/coverage.xml
coverage report
exit $ret
