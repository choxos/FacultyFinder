I want to create a website for helping future students find their ideal faculty, named FacultyFinder. To do so, I have started from Department of Health Research Methods, Evidence, and Impact (HEI) at McMaster University. I have the data from the university website, but I have validated 20 of them. You can find the data in data/mcmaster_hei_faculty.csv. 

FacultyFinder is a part of Xera DB. Xera DB projects use a same theme and a same structure. You can find the specifics of the theme and the structure in this folder: ~/Documents/Github/xeradb/shared_theme. I haven't created a specific theme for this project yet but create one with colors that can be related to this project and put it in css/themes/facultyfinder-theme.css. You can find the structure of other projects in ~/Documents/Github/OpenScienceTracker for OST project, ~/Documents/GitHub/CitingRetracted for PRCT project, and ~/Documents/GitHub/CIHRPT for CIHRPT project. Read each one carefully to understand the structure. Specifically, I want a website similar (in terms of the structure and the theme) to EvidenceDB which you can find in ~/Documents/Github/EvidenceDB/.

The structure of FacultyFinder is as follows:

- Main page: Shows a search bar and links to top 10 available universities. It should also show summary statistics of the data.
- Universities page: Shows the list of all available universities. The user can search and filter the list based on the university name and other attributes.
- Faculties page: Shows the list of all available professors. The user can search and filter the list based on the faculty name, research interests, and other attributes. Then, the user can click on a professor to see their profile page.
- AI assistant page: In this page, user can upload their CV and the AI assistant based on API of Claude, Geminie, ChatGPT, or Grok, will analyze the user's CV and provide a list of professors that are a good fit for the user. They should provide their own API key. If not, the user can pay for our own API key. The payment should be done through Stripe.
- An about page: This page should explain the purpose of the website and the data sources.
- API page: FacultyFinder should provide an API for other projects to use the data.

In the profile page of the professors, show the following information, based on the data in data/mcmaster_hei_faculty.csv:

- Full name (other names in parentheses): name column in the data
- Title: position column in the data (full time or part-time [full_time column] or adjunct [adjunct column])
- Degrees: degree column in the data (different degrees are separated by semicolon)
- Department: department column in the data
- University: university_code column in the data. Please note that I have created a list of all Canadian universities and gave them a unique ID in data/university_codes.csv. You can use this ID to link the university name, city, province/state, and country to the university ID. The university ID is university_code column in the data/university_codes.csv.
- Other departments: other_departments column in the data
- Memberships: memberships column in the data (different memberships are separated by semicolon)
- Director: director column in the data (different directors are separated by semicolon)
- Canada Research Chairs: canada_research_chair column in the data
- Research areas: research_areas column in the data (different research interests are separated by semicolon)
- University email: uni_email column in the data
- Other emails: other_email column in the data (different emails are separated by semicolon)
- Phone number: phone column in the data
- Fax number: fax column in the data
- Website: website column in the data
- Twitter/X: twitter column in the data. Please note that the twitter column contains the username of the professor's Twitter account. You should recreate the full URL of the professor's Twitter account: https://x.com/username.
- LinkedIn: linkedin column in the data. Please note that the linkedin column contains the username of the professor's LinkedIn account. You should recreate the full URL of the professor's LinkedIn account: https://www.linkedin.com/in/username.
- Google Scholar: google_scholar column in the data. Please note that the google_scholar column contains the username of the professor's Google Scholar account. You should recreate the full URL of the professor's Google Scholar account: https://scholar.google.com/citations?user=username.
- Scopus: scopus column in the data. Please note that the scopus column contains the username of the professor's Scopus account. You should recreate the full URL of the professor's Scopus account: https://www.scopus.com/authid/detail.uri?authorId=username.
- ResearchGate: researchgate column in the data. Please note that the researchgate column contains the username of the professor's ResearchGate account. You should recreate the full URL of the professor's ResearchGate account: https://www.researchgate.net/profile/username.
- ORCID: orcid column in the data. Please note that the orcid column contains the username of the professor's ORCID account. You should recreate the full URL of the professor's ORCID account: https://orcid.org/username.
- Academic.edu: academicedu column in the data. Please note that the academic_edu column contains the username of the professor's Academic.edu account. You should recreate the full URL of the professor's Academic.edu account: https://www.academic.edu/username.
- Web of Science: wos column in the data. Please note that the web_of_science column contains the username of the professor's Web of Science account. You should recreate the full URL of the professor's Web of Science account: https://www.webofscience.com/wos/author/record/username.

For the next stage, I want to use PubMed's Entrez API to search for the publications of the professors. You should create a function that takes a professor's name and returns the list of their publications. The search should be like this:

- To retrieve all their publications: (first_name last_name[Author])
- To retrieve all their publications when at the current university: (first_name last_name[Author] AND (university_name[Affiliation]))

Please note that I have provided first_name and last_name columns in the data/mcmaster_hei_faculty.csv. You can use them to search for the publications.

When adding a publication to the database, you should add all the information you can get from the PubMed search results. An example of the output of the PubMed search results is available in data/pubmed_example.txt. The postgres database (for production) or sqlite database (for development) should not have duplicate publications. To do so, the database should check the publications pmid (and if available, pmcid and doi). It is possible that when searching for another author, some of the results from PubMed are already in the database. We can use this to create network of collaborations between the professors, inside the university, nationally, and internationally.

Also, the database should have the information about the journals based on Scimago. I have downloaded the information from Scimago Journal & Country Rank (https://www.scimagojr.com/journalrank.php) and saved it in data/scimago_journals_comprehensive.csv. Using this data from scimago, link rank, sjr, sjr_best_quartile, and h_index of the journals to the publications in the database during different years. The scimago data has been restructured for different years. All the years from 1999 to 2025 are available, denoted by _year in the column name; for example, rank_2025, sjr_2025, sjr_best_quartile_2025, and h_index_2025. You should match the issn of the journals of publications to the issn of the journals in the scimago data based on the year of publication of the paper. Then, we can use this information to show the percentage of publications in Q1, Q2, Q3, and Q4 journals in the profile page of the professors. Also, mean (SD) and median (Q1, Q3; here Q1 means quartiles related to median) of rank and sjr of the journals of publications in the profile page of the professors.

Please read the guide carefully and create the website that is very professional and user-friendly.

Create a step-by-step todo list.

Let's GO!