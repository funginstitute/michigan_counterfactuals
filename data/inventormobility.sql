-- for inventor history, we want:
-- patent id, grant date, inventor_id, state, is control? (1/0)
-- assume that the inventor ids for the control set are in the 'tmp' table

select patent.id, year(patent.date), rawinventor.inventor_id, location.state
from tmp 
left join rawinventor on rawinventor.inventor_id = tmp.number
left join patent on patent.id = rawinventor.patent_id
left join rawlocation on rawlocation.id = rawinventor.rawlocation_id
left join location on location.id = rawlocation.location_id;
