from docxtpl import DocxTemplate

def create_cv_doc(user_data):
    document = DocxTemplate("CV_template1.docx")

    context = {
        'first_last_name': user_data.get('first_last_name', 'Name'),
        'description': user_data.get('description', 'Description'),
        'work_experiences': user_data.get('work_experiences', []),
        'educations': user_data.get('educations', []),
        'address': user_data.get('address', ''),
        'phone_number': user_data.get('phone_number', ''),
        'email': user_data.get('email', ''),
        'languages': user_data.get('languages', [])
    }

    document.render(context)
    return document

    print(len(document.tables))

    # Add Summary (Subheading 1)
    left_table = document.tables[0]
    left_cell = left_table.cell(0, 0)
    left_paragraphs = []

    summary_paragraph = left_cell.add_paragraph()
    summary_paragraph.add_run('Summary')
    left_paragraphs.append(summary_paragraph)

    # Add Description (Text 1)
    left_paragraphs.append(left_cell.add_paragraph())
    left_paragraphs[1].add_run(context['description'])

    # Initialize variables
    work_experience_index = 2
    education_index = 0
    right_paragraphs = []

    if work_experience_index >= len(left_paragraphs):
        left_paragraphs.append(left_cell.add_paragraph())

    for work in user_data["work_experiences"]:

        # Add Company name (Subheading 2)
        if work_experience_index >= len(left_paragraphs):
            left_paragraphs.append(left_cell.add_paragraph())

        left_paragraphs[work_experience_index].add_run(work['company_name'])
        work_experience_index += 1

        # Add Position (Subheading 3)
        if work_experience_index >= len(left_paragraphs):
            left_paragraphs.append(left_cell.add_paragraph())

        left_paragraphs[work_experience_index].add_run(work['position'])
        work_experience_index += 1

        # Add Job Dates (Subtitle 4)
        if work_experience_index >= len(left_paragraphs):
            left_paragraphs.append(left_cell.add_paragraph())

        left_paragraphs[work_experience_index].add_run(f"{work['start_date']} - {work['end_date']}")
        work_experience_index += 1

        # Add Job Description (Subtitle 5)
        if work_experience_index >= len(left_paragraphs):
            left_paragraphs.append(left_cell.add_paragraph())

        left_paragraphs[work_experience_index].add_run('Job Description')
        work_experience_index += 1

        if work_experience_index >= len(left_paragraphs):
            left_paragraphs.append(left_cell.add_paragraph())

        left_paragraphs[work_experience_index].add_run(work['job_description'])
        work_experience_index += 1

        # Add Achievements (Subtitle 6)
        if work_experience_index >= len(left_paragraphs):
            left_paragraphs.append(left_cell.add_paragraph())

        left_paragraphs[work_experience_index].add_run('Achievements')
        work_experience_index += 1

        # Add Achievements Text (Text 1)
        if work_experience_index >= len(left_paragraphs):
            left_paragraphs.append(left_cell.add_paragraph())

        left_paragraphs[work_experience_index].add_run(work['achievements'])
        work_experience_index += 1

        # Add Additional Achievements Text (Text 2)
        if work_experience_index >= len(left_paragraphs):
            left_paragraphs.append(left_cell.add_paragraph())

        left_paragraphs[work_experience_index].add_run(
            work.get('additional_achievements', ''))
        work_experience_index += 1

    # Calculate starting index for Education section
    education_index = work_experience_index + 2

    # Add new paragraphs until education_index is within bounds
    while education_index >= len(left_paragraphs):
        left_paragraphs.append(left_cell.add_paragraph())
        education_index += 1

    left_paragraphs[education_index].add_run('Education')
    education_index += 1

    # Education details
    for education in user_data["educations"]:
        # Add University Name (Subheading 2)
        if education_index >= len(left_paragraphs):
            left_paragraphs.append(left_cell.add_paragraph())

        left_paragraphs[-1].add_run(
            education['university_name'] if education['university_name'] else 'University Name')
        education_index += 1

        # Add Dates of Study (Subtitle 3)
        if education_index >= len(left_paragraphs):
            left_paragraphs.append(left_cell.add_paragraph())

        left_paragraphs[education_index].add_run(
            f"{education['start_date']} - {education['end_date']}")
        education_index += 1

        # Add Speciality and a line break if needed
        if education_index >= len(left_paragraphs):
            left_paragraphs.append(left_cell.add_paragraph())

        left_paragraphs[education_index].add_run(f"{education['speciality']}")
        education_index += 1

        # Add a line break if there are more education entries
        if user_data["educations"] and education != user_data["educations"][-1]:
            if education_index >= len(left_paragraphs):
                left_paragraphs.append(left_cell.add_paragraph())

            left_paragraphs[education_index].add_run('\n')
            education_index += 1

            # Add content to the right column
            right_cell = left_table.cell(0, 1)  # Replaced 'table' with 'left_table'

            # Add Details (Subheading 5)
            details = right_cell.add_paragraph()
            right_paragraphs.append(details)
            details.add_run('Details')

            # Add Residence, Phone, Email address (Text 1)
            residence = right_cell.add_paragraph(user_data.get('address'))
            right_paragraphs.append(residence)

            phone = right_cell.add_paragraph(user_data.get('phone_number'))
            right_paragraphs.append(phone)

            email = right_cell.add_paragraph(user_data.get('email'))
            right_paragraphs.append(email)

            # Add Languages heading
            languages_heading = right_cell.add_paragraph()
            languages_heading.add_run('Languages')
            right_paragraphs.append(languages_heading)

            # Iterate through languages
            for language in user_data["languages"]:
                language_proficiency = right_cell.add_paragraph(
                    f"{language['language']} - {language['proficiency_level']}"
                )
                right_paragraphs.append(language_proficiency)


