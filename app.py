import os
import tempfile
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import the main analyzer logic
from main import LexiDataSentinelEnhanced

app = FastAPI(title="LexiData-Sentinel API")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/analyze")
async def analyze_code(
    code_file: UploadFile = File(...),
    schema_file: UploadFile = File(...)
):
    """
    Accepts Python code and JSON schema files, runs LexiData-Sentinel,
    and returns the diagnostics in JSON format.
    """
    if not code_file.filename.endswith('.py'):
        raise HTTPException(status_code=400, detail="Code file must be a .py file")
    if not schema_file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="Schema file must be a .json file")

    code_content = await code_file.read()
    schema_content = await schema_file.read()

    # Create temporary files to pass to LexiDataSentinelEnhanced
    with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as tmp_code:
        tmp_code.write(code_content)
        tmp_code_path = tmp_code.name

    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp_schema:
        tmp_schema.write(schema_content)
        tmp_schema_path = tmp_schema.name

    try:
        # Initialize and run the analyzer
        sentinel = LexiDataSentinelEnhanced(
            source_path=tmp_code_path,
            schema_path=tmp_schema_path,
            verbose=False,
            auto_detect=True
        )
        
        # Suppress stdout to avoid polluting console, or just let it print
        success = sentinel.run()
        
        # Extract diagnostics
        diagnostics = []
        for diag in sentinel.diagnostics.diagnostics:
            diagnostics.append({
                "level": diag.level.value,
                "message": diag.message,
                "line": diag.line,
                "column": diag.column
            })
            
        return JSONResponse(content={
            "success": success,
            "diagnostics": diagnostics,
            "summary": sentinel.diagnostics.get_summary()
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up temporary files
        if os.path.exists(tmp_code_path):
            os.remove(tmp_code_path)
        if os.path.exists(tmp_schema_path):
            os.remove(tmp_schema_path)

# Serve static files for the frontend
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    # Ensure static directory exists
    os.makedirs("static", exist_ok=True)
    print("Starting LexiData-Sentinel Web App on http://localhost:8000")
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
