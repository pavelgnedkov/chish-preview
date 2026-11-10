#!/usr/bin/env python3
"""Проверка разметки раздела «Сведения» по алгоритму из Методических
рекомендаций Рособрнадзора (v8.9.1, раздел 5): для каждой страницы
/sveden/<подраздел>/ строится дерево помеченных тегов (ближайший помеченный
предок = родитель) и проверяется наличие обязательных тегов.
Обязательные = без «*» в таблицах рекомендаций (для общеобразовательной школы).
"""
import os, sys
from bs4 import BeautifulSoup

SITE = sys.argv[1]
REQ = {  # подраздел: [(родитель или None, тег), ...]
    "common": [(None, "copy"), (None, "fullName"), (None, "regDate"), ("uchredLaw", "nameUchred"), (None, "address"), (None, "workTime"),
               (None, "telephone"), (None, "email"), (None, "licenseDocLink"), (None, "addressPlaceSet"), (None, "addressPlacePrac"),
               (None, "addressPlacePodg"), (None, "addressPlaceGia")],
    "struct": [(None, "copy"), ("structOrgUprav", "name"), ("structOrgUprav", "fio"), ("structOrgUprav", "post"), ("structOrgUprav", "addressStr")],
    "document": [(None, "copy"), (None, "ustavDocLink"), (None, "localActStud"), (None, "localActOrder"), (None, "reportEduDocLink"),
                 (None, "priemDocLink"), (None, "modeDocLink"), (None, "tekKontrolDocLink"), (None, "perevodDocLink"), (None, "vozDocLink")],
    "education": [(None, "copy")] + [("eduAccred", t) for t in ("eduName", "eduProf", "eduLevel", "eduForm", "learningTerm", "eduPred", "eduPrac")]
                 + [(None, "languageEl"), (None, "eduChislenEl"), (None, "eduPriemEl"), (None, "eduPerevodEl")]
                 + [("eduOp", t) for t in ("eduName", "eduLevel", "eduProf", "eduForm", "opMain", "educationPlan", "educationRpd", "educationShedule", "eduPr", "methodology")],
    "eduStandarts": [(None, "copy"), (None, "eduFedDoc")],
    "managers": [(None, "copy")] + [("rucovodstvo", t) for t in ("fio", "post", "telephone", "email")] + [("rucovodstvoZam", t) for t in ("fio", "post", "telephone", "email")],
    "employees": [(None, "copy")] + [("teachingStaff", t) for t in ("fio", "post", "teachingDiscipline", "teachingLevel", "specExperience", "teachingOp")],
    "objects": [(None, "copy")] + [("purposeCab", t) for t in ("addressCab", "nameCab", "osnCab", "ovzCab")]
               + [("purposePrac", t) for t in ("addressPrac", "namePrac", "osnPrac", "ovzPrac")]
               + [("purposeLibr", t) for t in ("objName", "objAddress", "objSq", "objCnt", "objOvz")]
               + [("purposeSport", t) for t in ("objName", "objAddress", "objSq", "objOvz")]
               + [(None, "ovz"), (None, "purposeFacil"), (None, "purposeFacilOvz"), (None, "comNet"), (None, "comNetOvz"), (None, "erList")],
    "paid_edu": [(None, "copy"), (None, "paidEdu"), (None, "paidDog"), (None, "paidSt")],
    "budget": [(None, "copy"), (None, "finBFVolume"), (None, "finBRVolume"), (None, "finBMVolume"), (None, "finPVolume"),
               ("volume", "finYear"), ("volume", "finPost"), ("volume", "finRas"), (None, "finPlanDocLink")],
    "vacant": [(None, "copy")] + [("vacant", t) for t in ("eduName", "eduLevel", "eduCourse", "eduForm", "numberBFVacant", "numberBRVacant", "numberBMVacant", "numberPVacant")],
    "grants": [(None, "copy"), (None, "grant"), (None, "support")],
    "inter": [(None, "copy")] + [("internationalDog", t) for t in ("stateName", "orgName", "dogReg")],
    "catering": [(None, "copy")] + [("meals", t) for t in ("objName", "objAddress", "objSq", "objOvz")] + [("health", t) for t in ("objName", "objAddress", "objSq", "objOvz")],
}
bad = 0
for sub, req in REQ.items():
    f = os.path.join(SITE, "sveden", sub, "index.html")
    soup = BeautifulSoup(open(f, encoding="utf-8"), "lxml")
    found = set()
    for el in soup.find_all(attrs={"itemprop": True}):
        par = el.find_parent(attrs={"itemprop": True})
        found.add((par["itemprop"] if par else None, el["itemprop"]))
        found.add(("*", el["itemprop"]))
    miss = [f"{p + '>' if p else ''}{t}" for p, t in req if (p, t) not in found and not (p is None and ("*", t) in found and t == "copy")]
    # copy в шапке может оказаться внутри другого помеченного блока — для корневых тегов допускаем любой уровень
    miss = [m for m in miss if not (">" not in m and ("*", m) in found)]
    print(f"{'OK ' if not miss else 'ERR'} /sveden/{sub}/ — тегов {len({t for p, t in found if p != '*'})}" + (f"; нет: {', '.join(miss)}" if miss else ""))
    bad += bool(miss)
sys.exit(1 if bad else 0)
