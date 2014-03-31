import sys
import os

for arg in sys.argv[1:]:
    os.system('mysql -h 169.229.7.251 -u root -p330Ablumhall uspto -e "\
            select patent.id, location.state, inventor.id from patent, rawlocation, rawinventor, inventor, location where patent.id = {0} \
            and rawinventor.patent_id = patent.id \
            and rawlocation.id = rawinventor.rawlocation_id \
            and location.id = rawlocation.location_id \
            and inventor.id = rawinventor.inventor_id;"'.format(arg))
