from fastapi import FastAPI
from fastapi import File, UploadFile, Form, Request
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from PIL import Image, UnidentifiedImageError
from io import BytesIO
import anyio
from model import generate_embeddings
app = FastAPI()


# Add CORS. This middleware allows cross-origin requests to the API,
# which may be necessary if the client application is running on a different domain or port.
app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"],
)

# All Functions below
async def root():
    return {"message": "Hello World"}

def health_check():
    return{"status":"OK"}

async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code = exc.status_code,
        content = {"error": exc.detail}
    )
    

async def upload_image(reference_image: UploadFile = Form(...), images: List[UploadFile] = File(...)):
    # In FastAPI, the ... syntax is used to indicate that a parameter is required and cannot be omitted.
    # same as reference_image: UploadFile = Form(required=True)
    
    # Implement the logic to handle reference image and other uploaded images
    # pre-process images: resize, scale_down etc.. which can be used by PyTorch pre-trained image embedding models
    # Generate embeddings for reference image and other images
    # Return the embeddings in a structured format (JSON)

    try:
        # Read reference image      
        reference_contents = await anyio.to_thread.run_sync(lambda: anyio.run(reference_image.read))
        reference_image = Image.open(BytesIO(reference_contents)).convert("RGB")

        # Read other images with their Ids
        other_images = []
        other_images_filenames = []
        for image in images:
            contents = await anyio.to_thread.run_sync(lambda: anyio.run(image.read))
            pil_image = Image.open(BytesIO(contents)).convert("RGB")
            other_images.append(pil_image)
            other_images_filenames.append(image.filename)

        # Generate embedding for all images
        all_images = [reference_image] + other_images
        all_embeddings  = generate_embeddings(all_images)
        
        # Seperate reference_image embedding and other image embeddings
        reference_embedding = all_embeddings[0]
        other_embeddings = all_embeddings[1:]

        return {
            "reference_embedding": reference_embedding.tolist(),
            "other_embeddings": [
                {"id": image_id, "embedding":embedding.tolist()}
                for image_id, embedding in zip (other_images_filenames, other_embeddings)
            ]
        }
    except UnidentifiedImageError as e:
        raise HTTPException(status_code=400, detail=f"Invalid image file: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

# All endpoints below
@app.get("/")
async def root_endpoint():
    return await root()

#to check the status of the web api (fastApi) server
@app.get("/health_check")
def health_check_endpoint():
    return health_check()

@app.exception_handler(HTTPException)
async def http_exception_handler_endpoint(request: Request, exc: HTTPException):
    return http_exception_handler()

# to serve request from a Client App which uploads images
@app.post("/upload_image")
async def upload_image_endpoint(reference_image: UploadFile = Form(...), images: List[UploadFile] = File(...)):
    return await upload_image(reference_image, images)