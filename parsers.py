import requests
import re
from bs4 import BeautifulSoup
import markdown

def get_html(url_path):
    response = requests.get(
        url_path,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
        },
    )
    return response.text

def parse_vacancy(url_path):
    html_content = get_html(url_path)
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Initialize markdown string
    markdown = ""
        
    try:
        # Extract title
        title = soup.find('h1', {'data-qa': 'vacancy-title'})
        if title:
            markdown += f"# {title.text.strip()}\n\n"
        
        # Extract company name
        company = soup.find('a', {'data-qa': 'vacancy-company-name'})
        if company:
            markdown += f"**Компания:** {company.text.strip()}\n\n"
        
        # Extract location
        location = soup.find('p', {'data-qa': 'vacancy-view-location'})
        if location:
            markdown += f"**Местоположение:** {location.text.strip()}\n\n"
        
        # Extract salary
        salary = soup.find('div', {'data-qa': 'vacancy-salary'})
        if salary:
            markdown += f"**Зарплата:** {salary.text.strip()}\n\n"
        
        # Extract experience
        experience = soup.find('p', {'data-qa': 'vacancy-experience'})
        if experience:
            markdown += f"**Опыт работы:** {experience.text.strip()}\n\n"
        
        # Extract description
        description = soup.find('div', {'data-qa': 'vacancy-description'})
        if description:
            markdown += "## Описание вакансии\n\n"
            for p in description.find_all(['p', 'ul', 'ol']):
                if p.name == 'ul' or p.name == 'ol':
                    for li in p.find_all('li'):
                        markdown += f"- {li.text.strip()}\n"
                    markdown += "\n"
                else:
                    markdown += f"{p.text.strip()}\n\n"
        
        # Extract key skills
        key_skills = soup.find('div', {'data-qa': 'skills-element'})
        if key_skills:
            markdown += "## Ключевые навыки\n\n"
            for skill in key_skills.find_all('span', {'data-qa': 'bloko-tag__text'}):
                markdown += f"- {skill.text.strip()}\n"
            markdown += "\n"
        
        # Extract employment type
        employment = soup.find('p', {'data-qa': 'vacancy-view-employment-mode'})
        if employment:
            markdown += f"**Тип занятости:** {employment.text.strip()}\n\n"
        
        # Extract work schedule
        schedule = soup.find('p', {'data-qa': 'vacancy-view-work-schedule'})
        if schedule:
            markdown += f"**График работы:** {schedule.text.strip()}\n\n"
    
        parsed_content = markdown.strip()
        
        # Check if we've successfully parsed any structured content
        if parsed_content:
            return parsed_content
        else:
            # If no structured content was parsed, raise an exception to trigger the fallback
            raise ValueError("No structured content found")

    except Exception as e:
        # Fallback: return the full text content of the HTML
        print(f"Warning: Could not parse vacancy structure. Returning full text content. Error: {str(e)}")
        return soup.get_text(separator='\n\n', strip=True)

def parse_resume(url_path):
    html_content = get_html(url_path)
    soup = BeautifulSoup(html_content, 'html.parser')
    md_lines = []
    try:
        # Extract name and title
        name = soup.find('h1', class_='resume-header__title')
        title = soup.find('h2', class_='resume-header__position')
        if name:
            md_lines.append(f"# {name.text.strip()}\n")
        if title:
            md_lines.append(f"## {title.text.strip()}\n")

        # Extract personal info
        personal_info = soup.find('div', class_='resume-header__body')
        if personal_info:
            md_lines.append("\n### Личная информация\n")
            for item in personal_info.find_all('p'):
                md_lines.append(f"- {item.text.strip()}\n")

        # Extract experience
        experience = soup.find('div', {'data-qa': 'resume-block-experience'})
        if experience:
            md_lines.append("\n### Опыт работы\n")
            for job in experience.find_all('div', class_='resume-block-item-gap'):
                company = job.find('div', class_='bloko-text')
                position = job.find('div', {'data-qa': 'resume-block-experience-position'})
                period = job.find('div', class_='bloko-column bloko-column_xs-4 bloko-column_s-2 bloko-column_m-2 bloko-column_l-2')
                description = job.find('div', {'data-qa': 'resume-block-experience-description'})
                
                if company:
                    md_lines.append(f"#### {company.text.strip()}\n")
                if position:
                    md_lines.append(f"**{position.text.strip()}**")
                if period:
                    md_lines.append(f" | {period.text.strip()}\n")
                if description:
                    md_lines.append(f"{description.text.strip()}\n\n")

        # Extract education
        education = soup.find('div', {'data-qa': 'resume-block-education'})
        if education:
            md_lines.append("\n### Образование\n")
            for edu in education.find_all('div', class_='resume-block-item-gap'):
                institution = edu.find('div', class_='bloko-text')
                degree = edu.find('div', {'data-qa': 'resume-block-education-organization'})
                year = edu.find('div', class_='bloko-column bloko-column_xs-4 bloko-column_s-2 bloko-column_m-2 bloko-column_l-2')
                
                if institution:
                    md_lines.append(f"#### {institution.text.strip()}\n")
                if degree:
                    md_lines.append(f"**{degree.text.strip()}**")
                if year:
                    md_lines.append(f" | {year.text.strip()}\n")

        # Extract skills
        skills = soup.find('div', {'data-qa': 'skills-table'})
        if skills:
            md_lines.append("\n### Навыки\n")
            for skill in skills.find_all('span', class_='bloko-tag__section'):
                md_lines.append(f"- {skill.text.strip()}\n")

        # Extract additional info
        additional_info = soup.find('div', {'data-qa': 'resume-block-additional'})
        if additional_info:
            md_lines.append("\n### Дополнительная информация\n")
            md_lines.append(additional_info.text.strip() + "\n")

        parsed_content = ''.join(md_lines)
    
        if parsed_content.strip():
            return parsed_content
        else:
            # If no structured content was parsed, raise an exception to trigger the fallback
            raise ValueError("No structured content found")
    except Exception as e:
        # Fallback: return the full text content of the HTML
        print(f"Warning: Could not parse resume structure. Returning full text content. Error: {str(e)}")
        return soup.get_text(separator='\n\n', strip=True)
    
