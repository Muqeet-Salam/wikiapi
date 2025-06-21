from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

app = FastAPI()

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

@app.get("/api/outline")
async def get_country_outline(request: Request, country: str = None):
    """
    Fetches Wikipedia content for a given country and returns a Markdown outline of its headings.
    """
    if not country:
        raise HTTPException(status_code=400, detail="Country parameter is required")
    
    try:
        # Step 1: Get Wikipedia page URL for the country
        wikipedia_url = f"https://en.wikipedia.org/wiki/{country.replace(' ', '_')}"
        
        # Step 2: Fetch the page content
        headers = {
            "User-Agent": "GlobalEduCountryInfoAPI/1.0 (https://example.com)"
        }
        response = requests.get(wikipedia_url, headers=headers)
        response.raise_for_status()
        
        # Step 3: Parse the HTML and extract headings
        soup = BeautifulSoup(response.text, 'html.parser')
        
        content_div = soup.find(id="mw-content-text")
        if not content_div:
            raise HTTPException(status_code=404, detail="Could not find main content on Wikipedia page")
        
        headings = content_div.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        
        # Step 4: Generate Markdown outline
        markdown_outline = "## Contents\n\n"
        
        for heading in headings:
            if heading.get('id') in ['mw-navigation', 'p-lang-label']:
                continue
                
            level = int(heading.name[1])
            text = heading.get_text().strip()
            
            if not text or text.startswith('[edit]'):
                continue
                
            markdown_outline += f"{'#' * level} {text}\n\n"
        
        return {
            "country": country,
            "wikipedia_url": wikipedia_url,
            "markdown_outline": markdown_outline.strip(),
            "status": "success"
        }
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Country page not found on Wikipedia")
        raise HTTPException(status_code=500, detail=f"Error fetching Wikipedia page: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

# For Vercel serverless compatibility
def handler(request):
    from fastapi import Request
    from fastapi.responses import JSONResponse
    
    req = Request(scope=request)
    country = req.query_params.get("country")
    
    async def run():
        return await get_country_outline(req, country)
    
    response = run()
    return JSONResponse(content=response.body)

handler = Mangum(app)
