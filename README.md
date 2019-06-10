# pod
POD (PDF On Demand) is a microservice for generating PDFs out of HTML templates

## Usage

Make a POST request to `/` with the following fields:
* html
  * Should contain the HTML to be transformed as a string
* css (optional)
  * Should contain the CSS to be transformed as a string
