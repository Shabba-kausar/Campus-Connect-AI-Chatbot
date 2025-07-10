from django.core.management.base import BaseCommand
from bot.models import Category, CollegeData

class Command(BaseCommand):
    help = 'Populates the database with initial categories and college data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Populating database...')
        
        # Create categories
        categories = [
            {"name": "Admission", "description": "Information about admission procedures and eligibility"},
            {"name": "Academics", "description": "Information about academic programs and curriculum"},
            {"name": "Campus Life", "description": "Information about campus facilities and amenities"},
            {"name": "Hostel", "description": "Information about hostel facilities and rules"},
            {"name": "Clubs", "description": "Information about college clubs and societies"},
            {"name": "Events", "description": "Information about college events and festivals"},
            {"name": "Placements", "description": "Information about placement opportunities"},
            {"name": "Fees", "description": "Information about fees and scholarships"},
            {"name": "Faculty", "description": "Information about faculty and staff"},
            {"name": "Library", "description": "Information about library facilities"},
            {"name": "Canteen", "description": "Information about canteen facilities and food options"}
        ]
        
        created_categories = []
        for category_data in categories:
            category, created = Category.objects.get_or_create(
                name=category_data["name"],
                defaults={"description": category_data["description"]}
            )
            created_categories.append(category)
            self.stdout.write(f"{'Created' if created else 'Found'} category: {category.name}")
            
        # Create college data
        self.populate_admissions_data(created_categories[0])
        self.populate_academics_data(created_categories[1])
        self.populate_campus_data(created_categories[2])
        self.populate_hostel_data(created_categories[3])
        self.populate_clubs_data(created_categories[4])
        self.populate_events_data(created_categories[5])
        self.populate_placements_data(created_categories[6])
        self.populate_fees_data(created_categories[7])
        self.populate_faculty_data(created_categories[8])
        self.populate_library_data(created_categories[9])
        self.populate_canteen_data(created_categories[10])
        
        self.stdout.write(self.style.SUCCESS('Database population completed successfully!'))

    def populate_admissions_data(self, category):
        data_points = [
            {
                "question": "What are the eligibility criteria for B.Tech admission?",
                "answer": "Applicants must pass the Higher Secondary Examination with Physics, Chemistry, and Mathematics and must be residents of Assam.",
                "keywords": "eligibility, criteria, b.tech, admission, higher secondary, qualification"
            },
            {
                "question": "Does JEC accept lateral entry for diploma holders?",
                "answer": "Yes, diploma holders can apply for lateral entry to B.Tech programs via the Lateral Entrance Examination.",
                "keywords": "lateral entry, diploma holders, b.tech"
            },
            {
                "question": "What is the minimum percentage required for B.Tech admission?",
                "answer": "A minimum of 50% in PCM is required for general category students, with relaxations for SC/ST students.",
                "keywords": "minimum percentage, b.tech, admission, marks, requirement"
            },
            {
                "question": "What is the fee structure for B.Tech?",
                "answer": "The approximate annual fee is around ₹11,000, which includes tuition and miscellaneous charges.",
                "keywords": "fee structure, b.tech, tuition, cost, expenses"
            },
            {
                "question": "Are admissions based on merit?",
                "answer": "Yes, admissions are merit-based, determined by entrance exam scores and academic qualifications.",
                "keywords": "merit, admission process, selection"
            }
        ]
        
        self._create_data_points(category, data_points)

    def populate_academics_data(self, category):
        data_points = [
            {
                "question": "What branches of engineering are offered at JEC?",
                "answer": "JEC offers B.Tech in Civil, Mechanical, Electrical, Computer Science, and Instrumentation Engineering.",
                "keywords": "branches, engineering, programs, departments, courses"
            },
            {
                "question": "What is the duration of the M.Tech program?",
                "answer": "The M.Tech program is typically two years long.",
                "keywords": "duration, m.tech, master, program length"
            },
            {
                "question": "Are internships mandatory for graduation?",
                "answer": "Internships are highly encouraged and often mandatory for specific programs.",
                "keywords": "internships, mandatory, graduation, requirement"
            },
            {
                "question": "How are final-year projects handled?",
                "answer": "Final-year students can choose from various projects in their respective fields, guided by faculty.",
                "keywords": "final-year, projects, thesis, dissertation, research"
            },
            {
                "question": "What is the grading system at JEC?",
                "answer": "JEC follows a semester-based grading system with CGPA.",
                "keywords": "grading system, cgpa, gpa, semester, marks"
            }
        ]
        
        self._create_data_points(category, data_points)

    def populate_campus_data(self, category):
        data_points = [
            {
                "question": "What facilities are available on campus?",
                "answer": "The campus includes classrooms, labs, library, canteen, sports grounds, hostels, an auditorium, and recreational spaces.",
                "keywords": "facilities, campus, amenities, infrastructure"
            },
            {
                "question": "Is there Wi-Fi available on campus?",
                "answer": "Yes, Wi-Fi is available in most areas of the campus, including hostels and academic buildings.",
                "keywords": "wifi, internet, connectivity, wireless"
            },
            {
                "question": "What sports facilities are available at JEC?",
                "answer": "Sports facilities include cricket and football grounds, basketball and volleyball courts, and indoor games like table tennis and chess.",
                "keywords": "sports, facilities, grounds, courts, games"
            },
            {
                "question": "Are there ATMs on campus?",
                "answer": "Yes, for student convenience, ATMs are available on campus.",
                "keywords": "atm, bank, cash, money, withdrawal"
            },
            {
                "question": "Is there a medical facility on campus?",
                "answer": "JEC provides a medical facility with a first-aid center and doctors on call.",
                "keywords": "medical, facility, health, doctor, first-aid"
            }
        ]
        
        self._create_data_points(category, data_points)

    def populate_hostel_data(self, category):
        data_points = [
            {
                "question": "How many hostels are there at JEC?",
                "answer": "Jorhat Engineering College has separate hostels for male and female students. There are 10 hostels in total: 2 for girls and 8 for boys.",
                "keywords": "hostels, number, boys, girls, accommodation"
            },
            {
                "question": "How many students share a room in the hostel?",
                "answer": "Typically, rooms are shared by two to four students, depending on availability and room allocation.",
                "keywords": "room sharing, occupancy, hostel room"
            },
            {
                "question": "Are the hostels furnished?",
                "answer": "Yes, each room is furnished with essentials like beds, study tables, wardrobes, and shelves for personal belongings.",
                "keywords": "furnished, furniture, hostel rooms, facilities"
            },
            {
                "question": "Is there a mess facility in the hostels?",
                "answer": "Yes, each hostel has a dedicated mess that provides regular meals to the students.",
                "keywords": "mess, food, dining, meals, hostel"
            },
            {
                "question": "What are the hostel timings and curfew?",
                "answer": "Yes, there are set timings for hostel entry to ensure security, but timings may vary and are communicated to students. Girls Hostel has a fixed intime of 7pm.",
                "keywords": "hostel timings, curfew, entry, restrictions"
            }
        ]
        
        self._create_data_points(category, data_points)

    def populate_clubs_data(self, category):
        data_points = [
            {
                "question": "What clubs are available at JEC?",
                "answer": "The college has a variety of clubs, including cultural clubs (RAMDHENU, DHWANY, Mukta, Jetuka), Fotokraft for photography, TRENDZ for modeling, Roboworld for robotics, GDGC, D-Code, and GLUG for coding, among others.",
                "keywords": "clubs, organizations, societies, student groups"
            },
            {
                "question": "How can I join a club at JEC?",
                "answer": "To join a club, you can connect with club coordinators during club sign-up events or reach out to the student affairs office for guidance.",
                "keywords": "join club, membership, sign-up, registration"
            },
            {
                "question": "What is the RAMDHENU club?",
                "answer": "RAMDHENU is a cultural club celebrating Assamese folk culture, especially focusing on traditional music and dance.",
                "keywords": "ramdhenu, cultural club, assamese, folk culture"
            },
            {
                "question": "What is Roboworld?",
                "answer": "Roboworld is the college's robotics club, where students can learn about and work on robotics projects.",
                "keywords": "roboworld, robotics, robot, tech club"
            },
            {
                "question": "What coding clubs are available at JEC?",
                "answer": "There are several coding clubs, including GDGC (Google Developer Group on Campus JEC), D-Code, and GLUG (the open-source software club).",
                "keywords": "coding clubs, programming, software, gdgc, d-code, glug"
            }
        ]
        
        self._create_data_points(category, data_points)

    def populate_events_data(self, category):
        data_points = [
            {
                "question": "What major events are organized at JEC?",
                "answer": "JEC organizes various events including cultural fests, technical fests, departmental symposiums, sports tournaments, and alumni meets throughout the academic year.",
                "keywords": "events, festivals, functions, programs, celebrations"
            },
            {
                "question": "Does JEC have a cultural fest?",
                "answer": "Yes, JEC hosts an annual cultural fest featuring various events and activities including music, dance, drama, and literary competitions.",
                "keywords": "cultural fest, festival, cultural events"
            },
            {
                "question": "Is there a technical fest at JEC?",
                "answer": "Yes, the annual tech fest features competitions, workshops, and exhibitions in various fields of engineering.",
                "keywords": "technical fest, tech fest, engineering events"
            },
            {
                "question": "What sports events are organized at JEC?",
                "answer": "JEC organizes various sports tournaments including cricket, football, volleyball, basketball, athletics, and indoor games throughout the year.",
                "keywords": "sports events, tournaments, competitions, games"
            },
            {
                "question": "Are there any workshops organized for students?",
                "answer": "Yes, various departments and clubs organize workshops on technical skills, soft skills, entrepreneurship, and other topics throughout the academic year.",
                "keywords": "workshops, training, seminars, skill development"
            }
        ]
        
        self._create_data_points(category, data_points)

    def populate_placements_data(self, category):
        data_points = [
            {
                "question": "What is the role of the Training and Placement Cell?",
                "answer": "The cell connects students with recruiters, arranges internships, and conducts pre-placement training.",
                "keywords": "training, placement cell, recruitment, career"
            },
            {
                "question": "What companies visit JEC for campus placements?",
                "answer": "Leading companies across IT, core engineering, and public sectors visit JEC for recruitment.",
                "keywords": "companies, recruiters, campus placements, job"
            },
            {
                "question": "What is the average placement percentage at JEC?",
                "answer": "JEC has a strong placement record; contact the placement cell for specific percentages.",
                "keywords": "placement percentage, statistics, employment rate"
            },
            {
                "question": "Do students get internships during their courses?",
                "answer": "Yes, internships are encouraged and often facilitated through the placement cell.",
                "keywords": "internships, industrial training, practical experience"
            },
            {
                "question": "What is the placement process at JEC?",
                "answer": "The process includes pre-placement talks, written tests, group discussions, and personal interviews.",
                "keywords": "placement process, recruitment procedure, selection"
            }
        ]
        
        self._create_data_points(category, data_points)

    def populate_fees_data(self, category):
        data_points = [
            {
                "question": "What is the fee structure for B.Tech at JEC?",
                "answer": "The approximate annual fee is around ₹11,000, which includes tuition and miscellaneous charges.",
                "keywords": "fee structure, b.tech, tuition, cost"
            },
            {
                "question": "What are the fees for M.Tech at JEC?",
                "answer": "M.Tech fees vary by specialization; contact the administration for a detailed breakdown.",
                "keywords": "m.tech fees, masters, postgraduate, tuition"
            },
            {
                "question": "What payment methods are available for fees?",
                "answer": "Fees can be paid via online banking, debit/credit cards, and other digital payment modes.",
                "keywords": "payment methods, fee payment, transaction"
            },
            {
                "question": "Are there installment options for fee payment?",
                "answer": "Yes, installment options are available; consult the finance office for specific terms.",
                "keywords": "installment, payment plan, fee structure"
            },
            {
                "question": "What scholarships are available for students?",
                "answer": "Scholarships include merit-based, need-based, and government-aided options for eligible students.",
                "keywords": "scholarships, financial aid, grants, assistance"
            }
        ]
        
        self._create_data_points(category, data_points)

    def populate_faculty_data(self, category):
        data_points = [
            {
                "question": "How many faculty members are there in each department?",
                "answer": "Faculty numbers vary by department; detailed lists are available in the academic office.",
                "keywords": "faculty members, professors, teachers, departments"
            },
            {
                "question": "Are there visiting professors at JEC?",
                "answer": "Yes, JEC occasionally invites visiting professors for specialized lectures and workshops.",
                "keywords": "visiting professors, guest faculty, lectures"
            },
            {
                "question": "What is the faculty-student ratio at JEC?",
                "answer": "JEC maintains a favorable faculty-student ratio to ensure quality learning; specifics vary by department.",
                "keywords": "faculty-student ratio, class size, teaching quality"
            },
            {
                "question": "How do faculty members support student projects?",
                "answer": "Faculty members guide, mentor, and evaluate students' project work throughout the year.",
                "keywords": "faculty support, projects, mentorship, guidance"
            },
            {
                "question": "Are there mentorship programs available?",
                "answer": "Students are assigned mentors within their departments for academic and career guidance.",
                "keywords": "mentorship, guidance, academic support, advice"
            }
        ]
        
        self._create_data_points(category, data_points)

    def populate_library_data(self, category):
        data_points = [
            {
                "question": "What are the library hours?",
                "answer": "The library operates during standard college hours, with extended hours during exams.",
                "keywords": "library hours, timing, opening, closing"
            },
            {
                "question": "How many books can a student borrow?",
                "answer": "Students can borrow up to three books, with extended limits during exam periods.",
                "keywords": "borrow books, library card, checkout limit"
            },
            {
                "question": "Is there access to digital resources?",
                "answer": "Not yet, but in the near future, students can have access to e-journals, digital libraries, and other online resources.",
                "keywords": "digital resources, e-journals, online library"
            },
            {
                "question": "Are there study rooms in the library?",
                "answer": "Yes, study rooms are available for individual and group study sessions.",
                "keywords": "study rooms, reading area, quiet space"
            },
            {
                "question": "Are there printing and photocopying facilities?",
                "answer": "Yes, printing and photocopying facilities are available for a minimal fee.",
                "keywords": "printing, photocopying, xerox, copy service"
            }
        ]
        
        self._create_data_points(category, data_points)

    def populate_canteen_data(self, category):
        data_points = [
            {
                "question": "Is there a canteen on campus?",
                "answer": "Yes, the campus includes a cafeteria offering a range of food options.",
                "keywords": "canteen, cafeteria, food, dining, eating"
            },
            {
                "question": "What are the canteen hours?",
                "answer": "The canteen typically operates from morning to evening during weekdays, with limited hours on weekends.",
                "keywords": "canteen hours, timing, opening, closing"
            },
            {
                "question": "What food options are available in the canteen?",
                "answer": "The canteen offers a variety of food options including North Indian, South Indian, and local Assamese cuisine, as well as snacks and beverages.",
                "keywords": "food options, menu, meals, dishes, cuisine"
            },
            {
                "question": "Is the food hygienic and nutritious?",
                "answer": "The mess is managed by experienced cooks under supervision, ensuring hygiene and nutritional balance in meals.",
                "keywords": "food hygiene, nutrition, cleanliness, quality"
            },
            {
                "question": "Are there special provisions for dietary requirements?",
                "answer": "Special arrangements may be made on request to the mess committee for students with specific dietary needs.",
                "keywords": "dietary requirements, special diet, food restrictions"
            }
        ]
        
        self._create_data_points(category, data_points)

    def _create_data_points(self, category, data_points):
        for point in data_points:
            data, created = CollegeData.objects.get_or_create(
                category=category,
                question=point["question"],
                defaults={
                    "answer": point["answer"],
                    "keywords": point["keywords"]
                }
            )
            self.stdout.write(f"{'Created' if created else 'Found'} data point: {data.question[:50]}...") 