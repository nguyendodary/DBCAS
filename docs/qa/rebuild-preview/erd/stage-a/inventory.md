# ERD Stage A inventory — every element exactly once

Canvas 3251 x 1677

## Shapes (62)
01. legend         bbox=(760,1522,2490,1633)
02. entity         bbox=(267,126,655,229) label=Role
03. entity         bbox=(2187,126,2574,229) label=Rubric
04. entity         bbox=(907,126,1295,229) label=Account
05. entity         bbox=(907,894,1295,997) label=Concept
06. entity         bbox=(2827,1278,3214,1381) label=Attempt
07. entity         bbox=(267,1278,655,1381) label=LLMCache
08. entity         bbox=(2187,510,2574,613) label=Question
09. entity         bbox=(907,510,1295,613) label=Assessment
10. entity         bbox=(1547,126,1934,229) label=UserProfile
11. entity         bbox=(2187,894,2574,997) label=SelectionLog
12. entity         bbox=(2827,894,3214,997) label=MCQOption
13. entity         bbox=(267,510,655,613) label=CourseLearningOutcome
14. entity         bbox=(1547,1278,1934,1381) label=CompetencyGap
15. entity         bbox=(2827,510,3214,613) label=SQLTestDataset
16. entity         bbox=(1547,894,1934,997) label=AssessmentSession
17. entity         bbox=(907,1278,1295,1381) label=ConceptCompetency
18. entity         bbox=(1547,510,1934,613) label=QuestionCandidate
19. ellipse        bbox=(35,529,246,593) label=clo id
20. ellipse        bbox=(2274,1024,2486,1088) label=log id
21. ellipse        bbox=(1634,256,1846,320) label=user id
22. ellipse        bbox=(354,256,566,320) label=role id
23. ellipse        bbox=(1634,1408,1846,1472) label=gap id
24. ellipse        bbox=(354,1408,566,1472) label=cache id
25. ellipse        bbox=(2274,35,2486,99) label=rubric id
26. ellipse        bbox=(2594,913,2806,977) label=option id
27. ellipse        bbox=(994,35,1206,99) label=account id
28. ellipse        bbox=(1314,913,1526,977) label=session id
29. ellipse        bbox=(2914,640,3126,704) label=dataset id
30. ellipse        bbox=(2914,1408,3126,1472) label=attempt id
31. ellipse        bbox=(674,913,886,977) label=concept id
32. ellipse        bbox=(1954,529,2166,593) label=question id
33. ellipse        bbox=(1634,419,1846,483) label=candidate id
34. ellipse        bbox=(994,1408,1206,1472) label=competency id
35. ellipse        bbox=(674,529,886,593) label=assessment id
36. diamond        bbox=(1339,138,1501,214) label=has
37. diamond        bbox=(1979,906,2141,982) label=logs
38. diamond        bbox=(1339,650,1501,726) label=seeds
39. diamond        bbox=(1659,1098,1821,1174) label=flags
40. diamond        bbox=(2619,714,2781,790) label=offers
41. diamond        bbox=(1339,522,1501,598) label=takes
42. diamond        bbox=(1339,1098,1501,1174) label=yields
43. diamond        bbox=(2299,1130,2461,1206) label=records
44. diamond        bbox=(1659,330,1821,406) label=authors
45. diamond        bbox=(699,714,861,790) label=maps to
46. diamond        bbox=(699,330,861,406) label=defines
47. diamond        bbox=(1019,714,1181,790) label=targets
48. diamond        bbox=(2299,714,2461,790) label=chosen in
49. diamond        bbox=(2939,1098,3101,1174) label=selected in
50. diamond        bbox=(699,138,861,214) label=assigned
51. diamond        bbox=(2619,522,2781,598) label=tested by
52. diamond        bbox=(1019,330,1181,406) label=configures
53. diamond        bbox=(2299,330,2461,406) label=graded by
54. diamond        bbox=(2619,986,2781,1062) label=answered in
55. diamond        bbox=(1339,778,1501,854) label=instantiates
56. diamond        bbox=(1339,1194,1501,1270) label=diagnosed in
57. diamond        bbox=(1659,714,1821,790) label=tagged with
58. diamond        bbox=(1979,602,2141,678) label=promoted to
59. diamond        bbox=(1019,1098,1181,1174) label=measured by
60. legend_rect    bbox=(808,1555,882,1600)
61. legend_diamond bbox=(1050,1546,1158,1610)
62. legend_key     bbox=(1394,1552,1505,1603)

## Connector segments (120)
001. (875,80) -> (958,80)
002. (1243,80) -> (1326,80)
003. (657,176) -> (697,176)
004. (863,176) -> (878,176)
005. (1323,176) -> (1337,176)
006. (1503,176) -> (1545,176)
007. (603,368) -> (697,368)
008. (863,368) -> (958,368)
009. (1243,368) -> (1657,368)
010. (1823,368) -> (2238,368)
011. (1195,480) -> (1326,480)
012. (1323,560) -> (1337,560)
013. (1503,560) -> (1518,560)
014. (2603,560) -> (2617,560)
015. (2783,560) -> (2825,560)
016. (248,562) -> (265,562)
017. (888,562) -> (905,562)
018. (2168,562) -> (2185,562)
019. (1963,640) -> (1977,640)
020. (2143,640) -> (2222,640)
021. (1883,656) -> (1966,656)
022. (2219,656) -> (2238,656)
023. (2523,656) -> (2606,656)
024. (1195,688) -> (1337,688)
025. (1503,688) -> (1598,688)
026. (2155,688) -> (2334,688)
027. (603,752) -> (697,752)
028. (863,752) -> (958,752)
029. (1243,752) -> (1657,752)
030. (1823,752) -> (2286,752)
031. (2475,752) -> (2617,752)
032. (2783,752) -> (2878,752)
033. (1515,800) -> (1646,800)
034. (1227,816) -> (1337,816)
035. (1503,816) -> (1598,816)
036. (2059,848) -> (2238,848)
037. (1963,944) -> (1977,944)
038. (888,946) -> (905,946)
039. (1528,946) -> (1545,946)
040. (2808,946) -> (2825,946)
041. (2603,1024) -> (2617,1024)
042. (2783,1024) -> (2878,1024)
043. (1883,1040) -> (1966,1040)
044. (2155,1104) -> (2606,1104)
045. (1243,1120) -> (1326,1120)
046. (1243,1136) -> (1337,1136)
047. (1503,1136) -> (1598,1136)
048. (1835,1168) -> (2297,1168)
049. (2463,1168) -> (2782,1168)
050. (1323,1232) -> (1337,1232)
051. (1503,1232) -> (1598,1232)
052. (2779,1312) -> (2825,1312)
053. (460,231) -> (460,254)
054. (460,1383) -> (460,1406)
055. (604,367) -> (604,508)
056. (604,615) -> (604,754)
057. (876,79) -> (876,178)
058. (956,79) -> (956,124)
059. (956,231) -> (956,370)
060. (956,751) -> (956,892)
061. (1100,101) -> (1100,124)
062. (1100,231) -> (1100,328)
063. (1100,408) -> (1100,508)
064. (1100,615) -> (1100,712)
065. (1100,792) -> (1100,892)
066. (1100,999) -> (1100,1096)
067. (1100,1176) -> (1100,1276)
068. (1100,1383) -> (1100,1406)
069. (1196,231) -> (1196,482)
070. (1196,687) -> (1196,892)
071. (1228,615) -> (1228,818)
072. (1244,79) -> (1244,124)
073. (1244,231) -> (1244,370)
074. (1244,751) -> (1244,892)
075. (1244,999) -> (1244,1122)
076. (1244,1135) -> (1244,1276)
077. (1324,79) -> (1324,178)
078. (1324,479) -> (1324,562)
079. (1324,1119) -> (1324,1234)
080. (1516,559) -> (1516,802)
081. (1596,615) -> (1596,690)
082. (1596,815) -> (1596,892)
083. (1596,999) -> (1596,1138)
084. (1596,1231) -> (1596,1276)
085. (1644,799) -> (1644,892)
086. (1740,231) -> (1740,254)
087. (1740,485) -> (1740,508)
088. (1740,999) -> (1740,1096)
089. (1740,1176) -> (1740,1276)
090. (1740,1383) -> (1740,1406)
091. (1836,999) -> (1836,1170)
092. (1884,615) -> (1884,658)
093. (1884,999) -> (1884,1042)
094. (1964,639) -> (1964,658)
095. (1964,943) -> (1964,1042)
096. (2060,847) -> (2060,904)
097. (2156,687) -> (2156,1106)
098. (2220,639) -> (2220,658)
099. (2236,367) -> (2236,508)
100. (2236,615) -> (2236,658)
101. (2236,847) -> (2236,892)
102. (2284,615) -> (2284,754)
103. (2332,615) -> (2332,690)
104. (2380,101) -> (2380,124)
105. (2380,231) -> (2380,328)
106. (2380,408) -> (2380,508)
107. (2380,615) -> (2380,712)
108. (2380,792) -> (2380,892)
109. (2380,999) -> (2380,1022)
110. (2476,615) -> (2476,754)
111. (2524,615) -> (2524,658)
112. (2604,559) -> (2604,658)
113. (2604,1023) -> (2604,1106)
114. (2780,1167) -> (2780,1314)
115. (2876,751) -> (2876,892)
116. (2876,1023) -> (2876,1276)
117. (3020,615) -> (3020,638)
118. (3020,999) -> (3020,1096)
119. (3020,1176) -> (3020,1276)
120. (3020,1383) -> (3020,1406)

## Text labels (112)
T001 entity     'Role' bbox=(430,165,493,189) size=31 weight=bold
T002 entity     'Rubric' bbox=(2334,165,2429,189) size=31 weight=bold
T003 entity     'Account' bbox=(1039,166,1162,189) size=31 weight=bold
T004 entity     'Concept' bbox=(1040,934,1162,964) size=31 weight=bold
T005 entity     'Attempt' bbox=(2958,1318,3083,1348) size=33 weight=bold
T006 entity     'LLMCache' bbox=(387,1317,537,1341) size=30 weight=bold
T007 entity     'Question' bbox=(2314,549,2447,576) size=31 weight=bold
T008 entity     'Assessment' bbox=(1014,550,1188,573) size=29 weight=bold
T009 entity     'UserProfile' bbox=(1660,165,1823,189) size=31 weight=bold
T010 entity     'SelectionLog' bbox=(2285,933,2476,964) size=31 weight=bold
T011 entity     'MCQOption' bbox=(2934,933,3108,964) size=32 weight=bold
T012 entity     'CourseLearningOutcome' bbox=(313,555,610,579) size=29 weight=bold
T013 entity     'CompetencyGap' bbox=(1618,1318,1863,1348) size=31 weight=bold
T014 entity     'SQLTestDataset' bbox=(2907,550,3135,576) size=30 weight=bold
T015 entity     'AssessmentSession' bbox=(1598,933,1882,957) size=29 weight=bold
T016 entity     'ConceptCompetency' bbox=(946,1318,1257,1348) size=31 weight=bold
T017 entity     'QuestionCandidate' bbox=(1598,549,1884,576) size=31 weight=bold
T018 key        'clo id' bbox=(112,552,169,570) size=25 weight=regular
T019 key        'log id' bbox=(2351,1046,2411,1070) size=27 weight=regular
T020 key        'user id' bbox=(1705,278,1776,296) size=25 weight=regular
T021 key        'role id' bbox=(427,278,494,296) size=26 weight=regular
T022 key        'gap id' bbox=(1707,1430,1774,1454) size=26 weight=regular
T023 key        'cache id' bbox=(417,1430,504,1448) size=24 weight=regular
T024 key        'rubric id' bbox=(2337,57,2424,75) size=25 weight=regular
T025 key        'option id' bbox=(2652,936,2749,960) size=26 weight=regular
T026 key        'account id' bbox=(1045,57,1156,75) size=25 weight=regular
T027 key        'session id' bbox=(1369,936,1472,954) size=24 weight=regular
T028 key        'dataset id' bbox=(2968,662,3073,680) size=25 weight=regular
T029 key        'attempt id' bbox=(2965,1430,3076,1454) size=26 weight=regular
T030 key        'concept id' bbox=(725,936,836,960) size=25 weight=regular
T031 key        'question id' bbox=(2001,552,2120,576) size=25 weight=regular
T032 key        'candidate id' bbox=(1675,441,1806,459) size=25 weight=regular
T033 key        'competency id' bbox=(1022,1430,1179,1454) size=25 weight=regular
T034 key        'assessment id' bbox=(706,552,854,570) size=23 weight=regular
T035 diamond    'has' bbox=(1407,169,1435,183) size=18 weight=regular
T036 diamond    'logs' bbox=(2045,936,2077,954) size=18 weight=regular
T037 diamond    'seeds' bbox=(1399,680,1443,694) size=17 weight=regular
T038 diamond    'flags' bbox=(1721,1128,1760,1146) size=19 weight=regular
T039 diamond    'offers' bbox=(2678,744,2723,761) size=19 weight=regular
T040 diamond    'takes' bbox=(1400,553,1442,567) size=18 weight=regular
T041 diamond    'yields' bbox=(1396,1128,1444,1146) size=20 weight=regular
T042 diamond    'records' bbox=(2351,1160,2410,1174) size=18 weight=regular
T043 diamond    'authors' bbox=(1710,361,1772,375) size=19 weight=regular
T044 diamond    'maps to' bbox=(748,745,814,762) size=19 weight=regular
T045 diamond    'defines' bbox=(752,361,810,378) size=18 weight=regular
T046 diamond    'targets' bbox=(1073,745,1129,762) size=18 weight=regular
T047 diamond    'chosen in' bbox=(2342,744,2419,758) size=18 weight=regular
T048 diamond    'selected in' bbox=(2978,1128,3063,1142) size=18 weight=regular
T049 diamond    'assigned' bbox=(746,169,817,187) size=18 weight=regular
T050 diamond    'tested by' bbox=(2665,553,2739,571) size=18 weight=regular
T051 diamond    'configures' bbox=(1059,361,1143,379) size=18 weight=regular
T052 diamond    'graded by' bbox=(2339,361,2423,379) size=19 weight=regular
T053 diamond    'answered in' bbox=(2652,1016,2749,1030) size=18 weight=regular
T054 diamond    'instantiates' bbox=(1374,809,1468,822) size=19 weight=regular
T055 diamond    'diagnosed in' bbox=(1369,1224,1472,1242) size=18 weight=regular
T056 diamond    'tagged with' bbox=(1693,744,1789,762) size=19 weight=regular
T057 diamond    'promoted to' bbox=(2010,633,2111,648) size=19 weight=regular
T058 diamond    'measured by' bbox=(1048,1128,1155,1146) size=18 weight=regular
T059 legend     'M' bbox=(621,624,643,643) size=28 weight=regular
T060 legend     'N' bbox=(621,480,639,499) size=28 weight=regular
T061 legend     'N' bbox=(675,146,693,165) size=28 weight=regular
T062 legend     'M' bbox=(973,96,995,115) size=28 weight=regular
T063 legend     'N' bbox=(973,864,991,883) size=28 weight=regular
T064 legend     '1' bbox=(974,240,983,259) size=26 weight=regular
T065 legend     'M' bbox=(1117,624,1139,643) size=28 weight=regular
T066 legend     'N' bbox=(1117,480,1135,499) size=28 weight=regular
T067 legend     'N' bbox=(1117,864,1135,883) size=28 weight=regular
T068 legend     'N' bbox=(1117,1248,1135,1267) size=28 weight=regular
T069 legend     '1' bbox=(1118,240,1127,259) size=26 weight=regular
T070 legend     '1' bbox=(1118,1008,1127,1027) size=26 weight=regular
T071 legend     '1' bbox=(1214,240,1222,259) size=26 weight=regular
T072 legend     '1' bbox=(1214,864,1222,883) size=26 weight=regular
T073 legend     '1' bbox=(1246,624,1254,643) size=26 weight=regular
T074 legend     'N' bbox=(1261,864,1278,883) size=28 weight=regular
T075 legend     'N' bbox=(1261,1248,1278,1267) size=28 weight=regular
T076 legend     '1' bbox=(1262,96,1270,115) size=26 weight=regular
T077 legend     '1' bbox=(1262,240,1270,259) size=26 weight=regular
T078 legend     '1' bbox=(1262,1008,1270,1027) size=26 weight=regular
T079 legend     '1' bbox=(1515,146,1524,165) size=26 weight=regular
T080 legend     'N' bbox=(1613,624,1630,643) size=28 weight=regular
T081 legend     'N' bbox=(1613,864,1630,883) size=28 weight=regular
T082 legend     'N' bbox=(1613,1248,1630,1267) size=28 weight=regular
T083 legend     '1' bbox=(1614,1008,1622,1027) size=26 weight=regular
T084 legend     'N' bbox=(1661,864,1678,883) size=28 weight=regular
T085 legend     'N' bbox=(1757,1248,1774,1267) size=28 weight=regular
T086 legend     '1' bbox=(1758,1008,1766,1027) size=26 weight=regular
T087 legend     '1' bbox=(1854,1008,1862,1027) size=26 weight=regular
T088 legend     '1' bbox=(1902,624,1910,643) size=26 weight=regular
T089 legend     '1' bbox=(1902,1008,1910,1027) size=26 weight=regular
T090 legend     'N' bbox=(2253,480,2270,499) size=28 weight=regular
T091 legend     'N' bbox=(2253,864,2270,883) size=28 weight=regular
T092 legend     '1' bbox=(2254,624,2262,643) size=26 weight=regular
T093 legend     'M' bbox=(2301,624,2323,643) size=28 weight=regular
T094 legend     '1' bbox=(2350,624,2358,643) size=26 weight=regular
T095 legend     'N' bbox=(2397,240,2414,259) size=28 weight=regular
T096 legend     'N' bbox=(2397,864,2414,883) size=28 weight=regular
T097 legend     '1' bbox=(2398,480,2406,499) size=26 weight=regular
T098 legend     '1' bbox=(2398,624,2406,643) size=26 weight=regular
T099 legend     '1' bbox=(2494,624,2502,643) size=26 weight=regular
T100 legend     '1' bbox=(2542,624,2550,643) size=26 weight=regular
T101 legend     'N' bbox=(2788,530,2806,549) size=28 weight=regular
T102 legend     'N' bbox=(2788,1282,2806,1301) size=28 weight=regular
T103 legend     'N' bbox=(2893,864,2910,883) size=28 weight=regular
T104 legend     'N' bbox=(2893,1248,2910,1267) size=28 weight=regular
T105 legend     'N' bbox=(3037,1248,3054,1267) size=28 weight=regular
T106 legend     '1' bbox=(3038,1008,3046,1027) size=26 weight=regular
T107 legend     'Entity' bbox=(902,1570,966,1595) size=26 weight=regular
T108 legend     'Relationship' bbox=(1180,1569,1323,1595) size=27 weight=regular
T109 legend_key 'key' bbox=(1435,1570,1465,1591) size=20 weight=regular
T110 legend     'Key attribute' bbox=(1525,1569,1676,1595) size=27 weight=regular
T111 legend_bold '1 = one, N / M = many' bbox=(1788,1570,2169,1595) size=28 weight=bold
T112 legend     '(M : N = many-to-many)' bbox=(2183,1570,2365,1594) size=24 weight=regular
