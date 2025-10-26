from flask import Flask, render_template, request, redirect
import os # importing operating system module
import requests
from bs4 import BeautifulSoup
from datetime import datetime

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True

def scrape_jobs():
    try:
        url = 'https://www.ycombinator.com/jobs'
        response = requests.get(url, timeout=30)

        if response.status_code != 200:
            print(f"Failed to fetch jobs: {response.status_code}")
            return []

        soup = BeautifulSoup(response.content, 'html.parser')
        jobs = soup.find_all('li', class_='my-2') # Find all job listings

        if not jobs:
                print("No jobs found on page")
                return []
        
        job_list = [] 
        for job in jobs: # Extract and return jobs in dictionary to html
            try:
                # Extract company name
                company = job.find('span', class_='block font-bold md:inline').text
                # Extract job title and link
                job_link_element = job.find('a', class_="font-semibold")
                job_title = job_link_element.text
                job_url = "https://www.ycombinator.com" + job_link_element['href']
                # Extract location (last div with break-all class)
                location = job.find('div', class_='break-all').text

                # Get job type (first whitespace-nowrap div)
                job_type_element = job.find('div', class_='whitespace-nowrap')
                job_type = job_type_element.text if job_type_element else "Not specified"

                job_list.append({
                    "company": company,
                    "job_title": job_title,
                    "job_link": job_url,
                    "location": location,
                    "job_type": job_type 
                })
            except AttributeError as e:
                print(f"Error parsing job: {e}")
                continue # Skip move onto next

        return job_list
    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error: {e}")
        return []

# Scrape once when app starts
jobs_data = scrape_jobs()

last_updated = datetime.now()

@app.route('/') # this decorator create the home route
def home():
    return render_template('home.html')

@app.route('/about') # decorator is like a function itself and it applies it's effect on the next   
def about():
    return render_template('about.html')

@app.route('/refresh')
def refresh():
    global jobs_data, last_updated
    jobs_data = scrape_jobs()
    return redirect('/jobs')

@app.route('/jobs')
def jobs():
    search_term = request.args.get('search', '').lower()        # Keyword search
    job_types = request.args.getlist('job_type')               # Checkboxes
    selected_location = request.args.get('location')           # Dropdown

    # All unique locations for dropdown
    locations = sorted(set(job['location'] for job in jobs_data))

    # Start with all jobs
    filtered_jobs = jobs_data

    # Filter by search term
    if search_term:
        filtered_jobs = [
            job for job in filtered_jobs
            if search_term in job['job_title'].lower() 
            or search_term in job['company'].lower() 
            or search_term in job['location'].lower()
        ]

    # Filter by job type
    if job_types:
        filtered_jobs = [
            job for job in filtered_jobs
            if job['job_type'] in job_types
        ]

    # Filter by location
    if selected_location:
        filtered_jobs = [
            job for job in filtered_jobs
            if job['location'] == selected_location
        ]

    return render_template(
        'jobs.html',
        jobs=filtered_jobs,
        locations=locations,
        last_updated=last_updated
    )


if __name__ == '__main__':
    # for deployment we use the environ
    # to make it work for both production and development
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)