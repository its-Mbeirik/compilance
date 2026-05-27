"""
Jalon 2 — Articles juridiques de référence pour les tests et la validation.
Textes basés sur l'AUSCGIE révisé (30 jan 2014) et le Code du Travail mauritanien
(Loi N° 2004-017 modifiée par 2009-027).
Ces articles sont utilisés quand les PDFs officiels ne sont pas disponibles.
"""
from ingestion.parser import RawArticle

# ---------------------------------------------------------------------------
# OHADA — Acte Uniforme relatif au Droit des Sociétés Commerciales (AUSCGIE)
# Juridiction : "ohada" | Code : "AUSCGIE"
# ---------------------------------------------------------------------------
AUSCGIE_ARTICLES: list[RawArticle] = [
    RawArticle(
        article_number="2",
        full_text=(
            "Article 2 : La société commerciale est celle qui est créée par deux ou plusieurs "
            "personnes qui conviennent, par un contrat, d'affecter à une activité des biens en "
            "numéraire ou en nature, ou de l'industrie, dans le but de partager le bénéfice ou de "
            "profiter de l'économie qui pourra en résulter. Elle peut être créée, dans les cas "
            "prévus par le présent Acte uniforme, par une seule personne, dénommée «associé unique»."
        ),
        hierarchy_path="Livre Premier > Titre 1 > Chapitre 1",
        jurisdiction="ohada",
        code_name="AUSCGIE",
        version_date="2014-05-05",
    ),
    RawArticle(
        article_number="13",
        full_text=(
            "Article 13 : Les statuts doivent, à peine de nullité, contenir les énonciations "
            "suivantes : 1° la forme de la société ; 2° la dénomination sociale ; 3° la nature et "
            "le domaine de l'activité, qui forme l'objet social ; 4° le siège social ; 5° la durée "
            "de la société ; 6° l'identité des apporteurs en numéraire, le montant des apports et "
            "le nombre de titres sociaux remis en contrepartie ; 7° l'identité des apporteurs en "
            "nature, la nature et l'évaluation de l'apport effectué par chacun d'eux et le nombre "
            "de titres sociaux remis en contrepartie ; 8° l'identité des bénéficiaires d'avantages "
            "particuliers et la nature de ceux-ci ; 9° le nombre et la valeur des titres sociaux "
            "émis, en distinguant les différentes catégories créées ; 10° les modalités de "
            "fonctionnement ; 11° le montant du capital social ; 12° les stipulations relatives à "
            "la répartition du résultat, à la constitution de réserves et à la répartition du boni "
            "de liquidation."
        ),
        hierarchy_path="Livre Premier > Titre 2 > Chapitre 1",
        jurisdiction="ohada",
        code_name="AUSCGIE",
        version_date="2014-05-05",
    ),
    RawArticle(
        article_number="25",
        full_text=(
            "Article 25 : Le siège social doit être localisé sur le territoire de l'un des États "
            "Parties. Il doit correspondre, soit au lieu du principal établissement de la société, "
            "soit à son siège administratif. Une boîte postale ne peut, en aucun cas, constituer "
            "un siège social. Les statuts peuvent prévoir les conditions dans lesquelles le siège "
            "social peut être transféré."
        ),
        hierarchy_path="Livre Premier > Titre 2 > Chapitre 2",
        jurisdiction="ohada",
        code_name="AUSCGIE",
        version_date="2014-05-05",
    ),
    RawArticle(
        article_number="28",
        full_text=(
            "Article 28 : La durée de la société est déterminée par les statuts sans qu'elle puisse "
            "excéder quatre-vingt-dix-neuf ans. Cette durée peut être prorogée par décision des "
            "associés prise dans les conditions requises pour la modification des statuts. La "
            "prorogation doit être décidée avant l'arrivée du terme statutaire. La société prend "
            "fin à l'expiration de la durée prévue par les statuts, sauf prorogation."
        ),
        hierarchy_path="Livre Premier > Titre 2 > Chapitre 3",
        jurisdiction="ohada",
        code_name="AUSCGIE",
        version_date="2014-05-05",
    ),
    RawArticle(
        article_number="311",
        full_text=(
            "Article 311 : Le capital social est divisé en parts sociales égales dont la valeur "
            "nominale est librement fixée par les associés dans les statuts. Le montant du capital "
            "social est fixé librement par les associés dans les statuts. Il ne peut être inférieur "
            "à un million (1 000 000) de francs CFA ou à toute autre somme fixée par l'État partie "
            "dont relève la société. Les parts sociales doivent être intégralement souscrites par "
            "les associés."
        ),
        hierarchy_path="Livre Deuxième > Titre 2 > Chapitre 1",
        jurisdiction="ohada",
        code_name="AUSCGIE",
        version_date="2014-05-05",
        country_override={"MR": {"capital_minimum_fcfa": 1000000, "note": "Dérogation nationale possible"}},
    ),
    RawArticle(
        article_number="312",
        full_text=(
            "Article 312 : Les parts sociales doivent être intégralement libérées lors de la "
            "souscription. La libération des parts représentant des apports en nature est réalisée "
            "au moment de leur souscription. Les parts représentant des apports en numéraire doivent "
            "être libérées intégralement lors de la signature des statuts ou lors de l'augmentation "
            "de capital."
        ),
        hierarchy_path="Livre Deuxième > Titre 2 > Chapitre 1",
        jurisdiction="ohada",
        code_name="AUSCGIE",
        version_date="2014-05-05",
    ),
    RawArticle(
        article_number="315",
        full_text=(
            "Article 315 : La société à responsabilité limitée est désignée par une dénomination "
            "sociale qui doit être immédiatement précédée ou suivie en caractères lisibles des "
            "mots «Société à responsabilité limitée» ou du sigle «SARL» et du montant du capital "
            "social. La dénomination sociale peut inclure le nom d'un ou de plusieurs associés."
        ),
        hierarchy_path="Livre Deuxième > Titre 2 > Chapitre 1",
        jurisdiction="ohada",
        code_name="AUSCGIE",
        version_date="2014-05-05",
    ),
    RawArticle(
        article_number="387",
        full_text=(
            "Article 387 : La société anonyme est une société dans laquelle les actionnaires ne "
            "sont responsables des dettes sociales qu'à concurrence de leurs apports et dont les "
            "droits des actionnaires sont représentés par des actions. Elle est désignée par une "
            "dénomination sociale. Le capital social de la société anonyme ne peut être inférieur "
            "à dix millions (10 000 000) de francs CFA."
        ),
        hierarchy_path="Livre Deuxième > Titre 3 > Chapitre 1",
        jurisdiction="ohada",
        code_name="AUSCGIE",
        version_date="2014-05-05",
    ),
    RawArticle(
        article_number="389",
        full_text=(
            "Article 389 : Les actions représentant des apports en numéraire sont libérées, lors "
            "de la souscription, d'un quart au moins de leur valeur nominale. La libération du "
            "surplus intervient, en une ou plusieurs fois, sur décision du conseil d'administration "
            "ou de l'administrateur général, dans un délai qui ne peut excéder trois ans à compter "
            "de l'immatriculation au Registre du Commerce et du Crédit Mobilier."
        ),
        hierarchy_path="Livre Deuxième > Titre 3 > Chapitre 2",
        jurisdiction="ohada",
        code_name="AUSCGIE",
        version_date="2014-05-05",
    ),
    RawArticle(
        article_number="395",
        full_text=(
            "Article 395 : Les actions sont librement cessibles, sauf restrictions prévues dans "
            "les statuts. Toute clause d'agrément doit s'appliquer à tout transfert d'actions, y "
            "compris les mutations à titre gratuit. Les actions ne peuvent être représentées par "
            "des titres nominatifs avant l'immatriculation au Registre du Commerce et du Crédit "
            "Mobilier."
        ),
        hierarchy_path="Livre Deuxième > Titre 3 > Chapitre 3",
        jurisdiction="ohada",
        code_name="AUSCGIE",
        version_date="2014-05-05",
    ),
]

# ---------------------------------------------------------------------------
# Code du Travail Mauritanien — Loi N° 2004-017
# Juridiction : "mauritania_labor" | Code : "CODE_TRAVAIL_MR"
# ---------------------------------------------------------------------------
CODE_TRAVAIL_ARTICLES: list[RawArticle] = [
    RawArticle(
        article_number="1",
        full_text=(
            "Article 1 : Les dispositions du présent Code s'appliquent aux relations de travail "
            "entre travailleurs et employeurs exerçant leurs activités sur le territoire de la "
            "République Islamique de Mauritanie, quelle que soit la nationalité des parties."
        ),
        hierarchy_path="Titre Préliminaire > Chapitre 1",
        jurisdiction="mauritania_labor",
        code_name="CODE_TRAVAIL_MR",
        version_date="2009-01-01",
    ),
    RawArticle(
        article_number="4",
        full_text=(
            "Article 4 : Le contrat de travail est la convention par laquelle une personne "
            "physique, le travailleur, s'engage à mettre son activité professionnelle sous la "
            "direction et l'autorité d'une autre personne physique ou morale, l'employeur, "
            "moyennant rémunération. Le contrat de travail est indépendant du statut juridique "
            "de l'employeur. Il ne peut être confondu avec d'autres contrats civils ou commerciaux."
        ),
        hierarchy_path="Titre 1 > Chapitre 1",
        jurisdiction="mauritania_labor",
        code_name="CODE_TRAVAIL_MR",
        version_date="2009-01-01",
    ),
    RawArticle(
        article_number="6",
        full_text=(
            "Article 6 : Tout contrat de travail individuel doit être conclu par écrit et établi "
            "en deux exemplaires originaux dont un est remis au travailleur. Le contrat doit "
            "préciser la nature et la durée du travail, le montant de la rémunération et ses "
            "modalités de paiement, le lieu de travail, et toute autre clause obligatoire définie "
            "par les conventions collectives applicables."
        ),
        hierarchy_path="Titre 1 > Chapitre 1",
        jurisdiction="mauritania_labor",
        code_name="CODE_TRAVAIL_MR",
        version_date="2009-01-01",
    ),
    RawArticle(
        article_number="10",
        full_text=(
            "Article 10 : La période d'essai est la phase initiale du contrat de travail pendant "
            "laquelle chacune des parties peut librement mettre fin à la relation de travail sans "
            "préavis ni indemnité. La période d'essai ne peut excéder six mois pour l'ensemble "
            "des travailleurs. Toutefois, pour les cadres et agents de maîtrise, elle peut être "
            "portée à douze mois au maximum. La période d'essai doit être expressément stipulée "
            "dans le contrat de travail."
        ),
        hierarchy_path="Titre 1 > Chapitre 2",
        jurisdiction="mauritania_labor",
        code_name="CODE_TRAVAIL_MR",
        version_date="2009-01-01",
    ),
    RawArticle(
        article_number="18",
        full_text=(
            "Article 18 : Le contrat de travail à durée déterminée est un contrat dont le terme "
            "est fixé avec précision dès la conclusion. Il doit être constaté par écrit. Lorsque "
            "sa durée est supérieure à trois mois, il doit être visé par l'Inspecteur du Travail "
            "territorialement compétent dans les huit jours de sa conclusion. À défaut de visa "
            "dans ce délai, le contrat est réputé conclu pour une durée indéterminée."
        ),
        hierarchy_path="Titre 1 > Chapitre 3",
        jurisdiction="mauritania_labor",
        code_name="CODE_TRAVAIL_MR",
        version_date="2009-01-01",
    ),
    RawArticle(
        article_number="52",
        full_text=(
            "Article 52 : La durée normale de travail des employés ou ouvriers de l'un ou l'autre "
            "sexe, de tout âge, dans tous les établissements publics ou privés, est fixée à "
            "quarante heures par semaine. Des décrets pris en Conseil des Ministres peuvent, "
            "après consultation des organisations professionnelles les plus représentatives, "
            "répartir différemment la durée hebdomadaire du travail dans certaines professions."
        ),
        hierarchy_path="Titre 2 > Chapitre 1",
        jurisdiction="mauritania_labor",
        code_name="CODE_TRAVAIL_MR",
        version_date="2009-01-01",
    ),
    RawArticle(
        article_number="153",
        full_text=(
            "Article 153 : Les enfants ne peuvent être employés dans aucune entreprise, même "
            "comme apprentis, avant l'âge de quatorze ans, sauf dérogation édictée par arrêté "
            "du Ministre chargé du Travail dans les cas et les conditions compatibles avec la "
            "santé et le développement normal de l'enfant. Toute infraction à ces dispositions "
            "est passible des sanctions prévues par le présent Code."
        ),
        hierarchy_path="Titre 5 > Chapitre 1",
        jurisdiction="mauritania_labor",
        code_name="CODE_TRAVAIL_MR",
        version_date="2009-01-01",
    ),
    RawArticle(
        article_number="154",
        full_text=(
            "Article 154 : L'âge minimum légal d'admission à l'emploi est fixé à quatorze ans. "
            "Les jeunes travailleurs âgés de quatorze à dix-huit ans ne peuvent être employés "
            "à des travaux susceptibles de nuire à leur santé, sécurité ou moralité. La liste "
            "de ces travaux est déterminée par arrêté du Ministre chargé du Travail après "
            "consultation des organisations syndicales les plus représentatives."
        ),
        hierarchy_path="Titre 5 > Chapitre 1",
        jurisdiction="mauritania_labor",
        code_name="CODE_TRAVAIL_MR",
        version_date="2009-01-01",
    ),
    RawArticle(
        article_number="178",
        full_text=(
            "Article 178 : Tout travailleur a droit, après douze mois de service effectif dans "
            "une même entreprise, à un congé annuel payé. La durée du congé est fixée à un jour "
            "et demi ouvrable par mois de travail effectif. Les congés payés sont calculés sur "
            "la base du salaire moyen des trois derniers mois précédant la date du départ en "
            "congé. L'employeur ne peut s'opposer à la prise effective du congé."
        ),
        hierarchy_path="Titre 5 > Chapitre 3",
        jurisdiction="mauritania_labor",
        code_name="CODE_TRAVAIL_MR",
        version_date="2009-01-01",
    ),
    RawArticle(
        article_number="195",
        full_text=(
            "Article 195 : En cas de licenciement abusif, le travailleur a droit à des dommages "
            "et intérêts correspondant au préjudice subi. Le tribunal compétent apprécie le "
            "caractère abusif ou non du licenciement en tenant compte notamment de la durée du "
            "service, de l'ancienneté, des usages de la profession et des circonstances du "
            "licenciement."
        ),
        hierarchy_path="Titre 6 > Chapitre 2",
        jurisdiction="mauritania_labor",
        code_name="CODE_TRAVAIL_MR",
        version_date="2009-01-01",
    ),
]

ALL_ARTICLES = AUSCGIE_ARTICLES + CODE_TRAVAIL_ARTICLES
