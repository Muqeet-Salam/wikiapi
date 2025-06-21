# api/outline.py

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
from bs4 import BeautifulSoup
from mangum import Mangum  # For AWS Lambda/Vercel compatibility

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

@app.get("/api/outline")
async def get_outline(country: str = Query(..., min_length=1)):
    country = country.strip().replace(" ", "_")
    url = f"https://en.wikipedia.org/wiki/{country}"

    async with httpx.AsyncClient() as client:
        res = await client.get(url)
        if res.status_code != 200:
            raise HTTPException(status_code=404, detail="Wikipedia page not found")

    soup = BeautifulSoup(res.text, "html.parser")
    headings = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])

    outline = ["## Contents"]
    for h in headings:
        level = int(h.name[1])
        text = h.get_text().strip()
        outline.append(f"{'#' * level} {text}")

    return {"outline": "\n\n".join(outline)}

# Vercel adapter
handler = Mangum(app)
