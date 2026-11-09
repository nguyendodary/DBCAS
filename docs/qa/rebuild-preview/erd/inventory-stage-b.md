# ERD Stage B inventory — final content delta

Canvas 3251 x 1677

## Shapes (58)
01. entity         bbox=(267,126,655,229) name=Role
02. entity         bbox=(907,126,1295,229) name=Account
03. entity         bbox=(1547,126,1935,229) name=UserProfile
04. entity         bbox=(2187,126,2575,229) name=SystemSetting
05. entity         bbox=(267,510,655,613) name=CourseLearningOutcome
06. entity         bbox=(907,510,1295,613) name=Assessment dashed
07. entity         bbox=(1547,510,1935,613) name=AssessmentConcept dashed
08. entity         bbox=(2187,510,2575,613) name=Question
09. entity         bbox=(907,894,1295,997) name=Concept
10. entity         bbox=(1547,894,1935,997) name=AssessmentSession
11. entity         bbox=(2187,894,2575,997) name=AssessmentQuestion dashed
12. entity         bbox=(2827,894,3215,997) name=MCQOption
13. entity         bbox=(267,1278,655,1381) name=AssessmentBlueprint dashed
14. entity         bbox=(907,1278,1295,1381) name=ConceptCompetency
15. entity         bbox=(1547,1278,1935,1381) name=CompetencyGap
16. entity         bbox=(2827,1278,3215,1381) name=Attempt
17. ellipse        bbox=(360,261,560,315) name=role_id
18. ellipse        bbox=(1000,40,1200,94) name=account_id
19. ellipse        bbox=(1640,261,1840,315) name=user_id
20. ellipse        bbox=(2280,261,2480,315) name=setting_key
21. ellipse        bbox=(40,534,240,588) name=clo_id
22. ellipse        bbox=(680,534,880,588) name=assessment_id
23. ellipse        bbox=(1580,419,1900,483) name=assessment_id, concept_id
24. ellipse        bbox=(1960,534,2160,588) name=question_id
25. ellipse        bbox=(2220,1024,2540,1088) name=assessment_id, question_id
26. ellipse        bbox=(680,918,880,972) name=concept_id
27. ellipse        bbox=(1320,918,1520,972) name=session_id
28. ellipse        bbox=(2600,918,2800,972) name=option_id
29. ellipse        bbox=(360,1413,560,1467) name=blueprint_id
30. ellipse        bbox=(2920,1413,3120,1467) name=attempt_id
31. ellipse        bbox=(1000,1413,1200,1467) name=competency_id
32. ellipse        bbox=(1640,1413,1840,1467) name=gap_id
33. diamond        bbox=(699,138,861,214) name=assigned
34. diamond        bbox=(1339,138,1501,214) name=has
35. diamond        bbox=(699,330,861,406) name=defines
36. diamond        bbox=(1659,330,1821,406) name=updates
37. diamond        bbox=(2599,522,2761,598) name=versions
38. diamond        bbox=(1339,522,1501,598) name=takes
39. diamond        bbox=(1019,330,1181,406) name=configures
40. diamond        bbox=(1979,650,2141,726) name=targets_legacy
41. diamond        bbox=(1659,714,1821,790) name=tagged with
42. diamond        bbox=(2619,714,2781,790) name=offers
43. diamond        bbox=(1019,714,1181,790) name=requires
44. diamond        bbox=(1339,778,1501,854) name=instantiates
45. diamond        bbox=(1979,906,2141,982) name=pools
46. diamond        bbox=(699,986,861,1062) name=uses
47. diamond        bbox=(1339,1098,1501,1174) name=yields
48. diamond        bbox=(1019,1098,1181,1174) name=measured by
49. diamond        bbox=(1659,1098,1821,1174) name=diagnosed
50. diamond        bbox=(2939,1098,3101,1174) name=selected in
51. diamond        bbox=(699,1098,861,1174) name=versions_legacy
52. diamond        bbox=(2299,1130,2461,1206) name=records
53. diamond        bbox=(1339,1194,1501,1270) name=targets
54. legend         bbox=(560,1522,3000,1633)
55. legend_rect    bbox=(808,1555,882,1600)
56. legend_diamond bbox=(1050,1546,1158,1610)
57. legend_key     bbox=(1394,1552,1505,1603)
58. legend_legacy  bbox=(2470,1555,2522,1600)

## Connector polylines (42)
001. (655,176) -> (699,176)
002. (861,176) -> (907,176)
003. (1295,176) -> (1339,176)
004. (1501,176) -> (1547,176)
005. (958,229) -> (958,368) -> (861,368)
006. (699,368) -> (604,368) -> (604,510)
007. (1250,229) -> (1250,480) -> (1339,480) -> (1339,560)
008. (1501,560) -> (1535,560) -> (1535,850) -> (1700,850) -> (1700,894)
009. (2250,613) -> (2250,752) -> (1821,752)
010. (1659,752) -> (1300,752) -> (1300,945) -> (1295,945)
011. (2500,613) -> (2500,752) -> (2619,752)
012. (2781,752) -> (2850,752) -> (2850,894)
013. (3020,997) -> (3020,1098)
014. (3020,1174) -> (3020,1278)
015. (1850,997) -> (1850,1100) -> (2100,1100) -> (2100,1168) -> (2299,1168)
016. (2461,1168) -> (2700,1168) -> (2700,1278)
017. (1600,997) -> (1600,1136) -> (1501,1136)
018. (1339,1136) -> (1200,1136) -> (1200,1278)
019. (1100,997) -> (1100,1098)
020. (1100,1174) -> (1100,1278)
021. (1740,997) -> (1740,1098)
022. (1740,1174) -> (1740,1278)
023. (1250,997) -> (1250,1232) -> (1339,1232)
024. (1501,1232) -> (1600,1232) -> (1600,1278)
025. (2575,535) -> (2615,535) -> (2615,560) -> (2599,560)
026. (2575,613) -> (2575,630) -> (2795,630) -> (2795,560) -> (2761,560)
027. (1295,229) -> (1295,300) -> (1500,300) -> (1500,368) -> (1657,368)
028. (1821,368) -> (2250,368) -> (2250,229)
029. (1019,894) -> (1019,752)
030. (1181,894) -> (1181,752)
031. (1100,229) -> (1100,330)
032. (1100,406) -> (1100,510)
033. (1250,613) -> (1250,688) -> (1979,688)
034. (2141,688) -> (2200,688) -> (2200,750) -> (1900,750) -> (1900,613)
035. (1250,613) -> (1250,700) -> (1979,700) -> (1979,944)
036. (2141,944) -> (2187,944)
037. (907,613) -> (620,613) -> (620,1136) -> (699,1136)
038. (861,1136) -> (900,1136) -> (900,1200) -> (600,1200) -> (600,1278)
039. (1150,613) -> (1150,816) -> (1339,816)
040. (1501,816) -> (1530,816) -> (1530,920) -> (1547,920)
041. (1650,997) -> (1650,1024) -> (861,1024)
042. (699,1024) -> (500,1024) -> (500,1278)

## Text labels (106)
T001 entity     'Role' bbox=(426,165,496,189) size=34 weight=bold color=#222222
T002 entity     'Account' bbox=(1036,165,1166,189) size=33 weight=bold color=#222222
T003 entity     'UserProfile' bbox=(1656,165,1826,189) size=33 weight=bold color=#222222
T004 entity     'SystemSetting' bbox=(2269,165,2493,189) size=33 weight=bold color=#222222
T005 entity     'CourseLearningOutcome' bbox=(292,549,630,573) size=29 weight=bold color=#222222
T006 entity     'Assessment' bbox=(1006,549,1196,573) size=32 weight=bold color=#222222
T007 legacy_tag 'LEGACY' bbox=(1199,583,1281,601) size=14 weight=bold color=#666666
T008 entity     'AssessmentConcept' bbox=(1581,549,1901,573) size=32 weight=bold color=#222222
T009 legacy_tag 'LEGACY' bbox=(1839,583,1921,601) size=14 weight=bold color=#666666
T010 entity     'Question' bbox=(2310,549,2452,573) size=34 weight=bold color=#222222
T011 entity     'Concept' bbox=(1036,933,1166,957) size=33 weight=bold color=#222222
T012 entity     'AssessmentSession' bbox=(1584,933,1898,957) size=33 weight=bold color=#222222
T013 entity     'AssessmentQuestion' bbox=(2216,933,2546,957) size=32 weight=bold color=#222222
T014 legacy_tag 'LEGACY' bbox=(2479,967,2561,985) size=14 weight=bold color=#666666
T015 entity     'MCQOption' bbox=(2931,933,3111,957) size=33 weight=bold color=#222222
T016 entity     'AssessmentBlueprint' bbox=(295,1317,627,1341) size=32 weight=bold color=#222222
T017 legacy_tag 'LEGACY' bbox=(559,1351,641,1369) size=14 weight=bold color=#666666
T018 entity     'ConceptCompetency' bbox=(939,1317,1263,1341) size=33 weight=bold color=#222222
T019 entity     'CompetencyGap' bbox=(1612,1317,1870,1341) size=33 weight=bold color=#222222
T020 entity     'Attempt' bbox=(2960,1317,3082,1341) size=32 weight=bold color=#222222
T021 key        'role_id' bbox=(425,279,495,297) size=25 weight=regular color=#222222
T022 key        'account_id' bbox=(1043,58,1157,76) size=24 weight=regular color=#222222
T023 key        'user_id' bbox=(1702,279,1778,297) size=23 weight=regular color=#222222
T024 key        'setting_key' bbox=(2320,279,2440,297) size=24 weight=regular color=#222222
T025 key        'clo_id' bbox=(110,552,170,570) size=24 weight=regular color=#222222
T026 key        'assessment_id' bbox=(701,552,859,570) size=24 weight=regular color=#222222
T027 key        'assessment_id, concept_id' bbox=(1620,442,1860,460) size=23 weight=regular color=#222222
T028 key        'question_id' bbox=(2000,552,2120,570) size=24 weight=regular color=#222222
T029 key        'assessment_id, question_id' bbox=(2257,1047,2503,1065) size=23 weight=regular color=#222222
T030 key        'concept_id' bbox=(723,936,837,954) size=24 weight=regular color=#222222
T031 key        'session_id' bbox=(1364,936,1476,954) size=24 weight=regular color=#222222
T032 key        'option_id' bbox=(2652,936,2748,954) size=24 weight=regular color=#222222
T033 key        'blueprint_id' bbox=(400,1431,520,1449) size=24 weight=regular color=#222222
T034 key        'attempt_id' bbox=(2964,1431,3076,1449) size=24 weight=regular color=#222222
T035 key        'competency_id' bbox=(1020,1431,1180,1449) size=24 weight=regular color=#222222
T036 key        'gap_id' bbox=(1705,1431,1775,1449) size=24 weight=regular color=#222222
T037 diamond    'assigned' bbox=(744,167,816,185) size=18 weight=regular color=#222222
T038 diamond    'has' bbox=(1406,167,1434,185) size=18 weight=regular color=#222222
T039 diamond    'defines' bbox=(751,359,809,377) size=18 weight=regular color=#222222
T040 diamond    'updates' bbox=(1708,359,1772,377) size=18 weight=regular color=#222222
T041 diamond    'versions' bbox=(2646,551,2714,569) size=18 weight=regular color=#222222
T042 diamond    'takes' bbox=(1398,551,1442,569) size=18 weight=regular color=#222222
T043 diamond    'configures' bbox=(1058,359,1142,377) size=18 weight=regular color=#222222
T044 diamond    'targets' bbox=(2032,679,2088,697) size=18 weight=regular color=#222222
T045 diamond    'tagged with' bbox=(1694,743,1786,761) size=18 weight=regular color=#222222
T046 diamond    'offers' bbox=(2678,743,2722,761) size=18 weight=regular color=#222222
T047 diamond    'requires' bbox=(1068,743,1132,761) size=18 weight=regular color=#222222
T048 diamond    'instantiates' bbox=(1374,807,1466,825) size=18 weight=regular color=#222222
T049 diamond    'pools' bbox=(2038,935,2082,953) size=19 weight=regular color=#222222
T050 diamond    'uses' bbox=(761,1015,799,1033) size=18 weight=regular color=#222222
T051 diamond    'yields' bbox=(1397,1127,1443,1145) size=18 weight=regular color=#222222
T052 diamond    'measured by' bbox=(1048,1127,1152,1145) size=18 weight=regular color=#222222
T053 diamond    'diagnosed' bbox=(1698,1127,1782,1145) size=18 weight=regular color=#222222
T054 diamond    'selected in' bbox=(2977,1127,3063,1145) size=18 weight=regular color=#222222
T055 diamond    'versions' bbox=(746,1127,814,1145) size=18 weight=regular color=#222222
T056 diamond    'records' bbox=(2350,1159,2410,1177) size=18 weight=regular color=#222222
T057 diamond    'targets' bbox=(1392,1223,1448,1241) size=18 weight=regular color=#222222
T058 card       'N' bbox=(668,145,687,164) size=28 weight=bold color=#222222
T059 card       'M' bbox=(873,145,895,164) size=27 weight=bold color=#222222
T060 card       '1' bbox=(1305,145,1319,164) size=27 weight=bold color=#222222
T061 card       '1' bbox=(1508,145,1522,164) size=27 weight=bold color=#222222
T062 card       '1' bbox=(966,240,980,259) size=27 weight=bold color=#222222
T063 card       'N' bbox=(612,480,631,499) size=28 weight=bold color=#222222
T064 card       '1' bbox=(1258,240,1272,259) size=27 weight=bold color=#222222
T065 card       'N' bbox=(1708,858,1727,877) size=28 weight=bold color=#222222
T066 card       'M' bbox=(2258,715,2280,734) size=27 weight=bold color=#222222
T067 card       'N' bbox=(1308,905,1327,924) size=28 weight=bold color=#222222
T068 card       '1' bbox=(2508,715,2522,734) size=27 weight=bold color=#222222
T069 card       'N' bbox=(2858,860,2877,879) size=28 weight=bold color=#222222
T070 card       '1' bbox=(3028,1010,3042,1029) size=27 weight=bold color=#222222
T071 card       'N' bbox=(3028,1240,3047,1259) size=28 weight=bold color=#222222
T072 card       '1' bbox=(1860,1010,1874,1029) size=27 weight=bold color=#222222
T073 card       'N' bbox=(2708,1240,2727,1259) size=28 weight=bold color=#222222
T074 card       '1' bbox=(1608,1040,1622,1059) size=27 weight=bold color=#222222
T075 card       'N' bbox=(1208,1240,1227,1259) size=28 weight=bold color=#222222
T076 card       '1' bbox=(1108,1040,1122,1059) size=27 weight=bold color=#222222
T077 card       'N' bbox=(1108,1240,1127,1259) size=28 weight=bold color=#222222
T078 card       '1' bbox=(1748,1010,1762,1029) size=27 weight=bold color=#222222
T079 card       'N' bbox=(1748,1240,1767,1259) size=28 weight=bold color=#222222
T080 card       '1' bbox=(1258,1040,1272,1059) size=27 weight=bold color=#222222
T081 card       'N' bbox=(1608,1240,1627,1259) size=28 weight=bold color=#222222
T082 card       '1' bbox=(2585,505,2599,524) size=27 weight=bold color=#222222
T083 card       'N' bbox=(2585,635,2604,654) size=28 weight=bold color=#222222
T084 card       '1' bbox=(1320,370,1334,389) size=27 weight=bold color=#222222
T085 card       'N' bbox=(2258,250,2277,269) size=28 weight=bold color=#222222
T086 card       'M' bbox=(1027,850,1049,869) size=27 weight=bold color=#222222
T087 card       'N' bbox=(1189,850,1208,869) size=28 weight=bold color=#222222
T088 card       '1' bbox=(1108,240,1122,259) size=27 weight=bold color=#222222
T089 card       'N' bbox=(1108,480,1127,499) size=28 weight=bold color=#222222
T090 card       '1' bbox=(1160,650,1174,669) size=27 weight=bold color=#222222
T091 card       'N' bbox=(1908,640,1927,659) size=28 weight=bold color=#222222
T092 card       '1' bbox=(1258,650,1272,669) size=27 weight=bold color=#222222
T093 card       'N' bbox=(2152,910,2171,929) size=28 weight=bold color=#222222
T094 card       '1' bbox=(730,625,744,644) size=27 weight=bold color=#222222
T095 card       'N' bbox=(608,1240,627,1259) size=28 weight=bold color=#222222
T096 card       'N' bbox=(1158,780,1177,799) size=28 weight=bold color=#222222
T097 card       '1' bbox=(1500,870,1514,889) size=27 weight=bold color=#222222
T098 card       'N' bbox=(1658,1015,1677,1034) size=28 weight=bold color=#222222
T099 card       '1' bbox=(508,1240,522,1259) size=27 weight=bold color=#222222
T100 legend     'Entity' bbox=(902,1570,966,1595) size=26 weight=regular color=#222222
T101 legend     'Relationship' bbox=(1180,1569,1323,1595) size=27 weight=regular color=#222222
T102 legend_key 'key' bbox=(1435,1570,1465,1591) size=20 weight=regular color=#222222
T103 legend     'Key attribute' bbox=(1525,1569,1676,1595) size=27 weight=regular color=#222222
T104 legend_bold '1 = one, N / M = many' bbox=(1788,1570,2169,1595) size=28 weight=bold color=#222222
T105 legend     '(M : N = many-to-many)' bbox=(2183,1570,2365,1594) size=24 weight=regular color=#222222
T106 legend     'Legacy table (historical rows only)' bbox=(2540,1570,2920,1595) size=25 weight=regular color=#222222
