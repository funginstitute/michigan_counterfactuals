select uspatentcitation.patent_id as citing, citation_id as cited, year(patent.date) as citing_year from tmp 
left join uspatentcitation on citation_id = tmp.number
left join patent on patent.id = patent_id
left join rawinventor on rawinventor.patent_id = uspatentcitation.patent_id
left join rawlocation on rawlocation.id = rawinventor.rawlocation_id
left join location on location.id = rawlocation.location_id
where
(location.state = 'AK' or location.state = 'CA' or location.state = 'CT'
  or location.state = 'MN' or location.state = 'MT' or location.state = 'ND'
  or location.state = 'NV' or location.state = 'OK' or location.state = 'WA' or location.state = 'WV');
