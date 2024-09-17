import streamlit as st
import json
from bs4 import BeautifulSoup
import re
from typing import List, Dict
from scrapfly import ScrapeConfig, ScrapflyClient
from loguru import logger as log
import os


# Initialize Scrapfly client with your API key
scrapfly_api_key =  os.getenv('SCRAPFLY')
scrapfly = ScrapflyClient(key=SCRAPFLY_KEY)

# Base config for Scrapfly
BASE_CONFIG = {
    "asp": True,  # Anti scraping protection bypass
    "headers": {
        "Accept-Language": "en-US,en;q=0.5"
    }
}

# Function to parse job postings
def parse_jobs(response) -> List[Dict]:
    """Parse job listings from the company's LinkedIn jobs page."""
    selector = response.selector
    jobs = []
    for element in selector.xpath("//ul[contains(@class, 'jobs-search__results-list')]/li"):
        try:
            link = element.xpath(".//a[contains(@class, 'base-card__full-link')]")
            post_url = link.attrib.get('href', None)
            job_title = element.xpath(".//h3/text()").get().strip()
            company_name = element.xpath(".//h4[contains(@class, 'base-search-card__subtitle')]/a/text()").get().strip()
            location = element.xpath(".//span[@class='job-search-card__location']/text()").get().strip()

            job_info = {
                "job_title": job_title,
                "company_name": company_name,
                "location": location,
                "link": post_url
            }
            jobs.append(job_info)
        except:
            continue
    return jobs

# Scrape the job listings from LinkedIn
def scrape_job_postings(company_name: str, position: str) -> List[Dict]:
    """Scrape LinkedIn jobs page for the company and check if the position exists."""
    company_page = company_name.replace(" ", "-")
    url = f"https://in.linkedin.com/jobs/{company_page}-jobs"
    to_scrape = ScrapeConfig(url, **BASE_CONFIG)

    # Perform the scraping
    response = scrapfly.scrape(to_scrape)
    jobs_data = parse_jobs(response)

    # Filter jobs based on the input position
    filtered_jobs = [job for job in jobs_data if position.lower() in job['job_title'].lower()]
    
    return filtered_jobs

# Streamlit app
def main():
    st.title("Job Position Scraper")
    st.write("Enter the company name and job position to check if job openings exist.")

    # Input fields for company name and position
    company_name = st.text_input("Company Name")
    position = st.text_input("Job Position")

    # When the user clicks the "Search Jobs" button
    if st.button("Search Jobs"):
        if not company_name or not position:
            st.error("Please provide both a company name and a job position.")
        else:
            # Scrape job postings
            with st.spinner('Searching for job openings...'):
                try:
                    job_postings = scrape_job_postings(company_name, position)
                    if job_postings:
                        st.success(f"Found {len(job_postings)} job opening(s) for '{position}' at {company_name}:")
                        for job in job_postings:
                            st.write(f"**Title:** {job['job_title']}")
                            st.write(f"**Company:** {job['company_name']}")
                            st.write(f"**Location:** {job['location']}")
                            st.write(f"[View Job Posting]({job['link']})")
                            st.markdown("---")
                    else:
                        st.warning(f"No job openings found for '{position}' at {company_name}.")
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")

# Run the app
if __name__ == "__main__":
    main()
