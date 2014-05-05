select tmp.number, inventor_id, assignee_id, patent.date, location.state from tmp
left join rawinventor on rawinventor.patent_id = tmp.number
left join rawassignee on rawassignee.patent_id = tmp.number
left join assignee on assignee.id = rawassignee.assignee_id
left join patent on patent.id = tmp.number
left join rawlocation on rawlocation.id = rawinventor.rawlocation_id
left join location on location.id = rawlocation.location_id
where
assignee.organization != '';
