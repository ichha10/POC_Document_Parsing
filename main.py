import os
import sys
import time
from typing import List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from vector_store import VectorStore
import pipeline
from schemas import GeneratedDocument

# Force UTF-8 on Windows just in case
if sys.platform.startswith("win"):
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    except Exception:
        pass

# ANSI Color Codes for terminal styling
BLUE = "\033[94m"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
UNDERLINE = "\033[4m"
RESET = "\033[0m"

OUTPUT_DIR = "data"
OUTPUT_MD = os.path.join(OUTPUT_DIR, "upgraded_document.md")
OUTPUT_PDF = os.path.join(OUTPUT_DIR, "upgraded_document.pdf")

def render_banner():
    """Prints a premium CLI banner."""
    print("=" * 85)
    print(f" {BOLD}{CYAN}XYZ SYSTEM - RAG DOCUMENT RECONSTRUCTION & SCHEMA MIGRATION POC{RESET} ")
    print("=" * 85)
    api_key_status = f"{GREEN}LOADED{RESET}" if os.getenv("GEMINI_API_KEY") else f"{YELLOW}OFFLINE / MOCK MODE{RESET}"
    print(f"Status: [ACTIVE] | Gemini API Key: {api_key_status}")
    print(f"Workspace: {BLUE}{os.getcwd()}{RESET}")
    print("=" * 85)
    print()

def create_env_template_if_missing():
    """Generates a template .env file if it doesn't exist."""
    if not os.path.exists(".env"):
        with open(".env", "w", encoding="utf-8") as f:
            f.write("# Enter your Google Gemini API Key below to enable Live LLM Mode\n")
            f.write("# If left blank, the pipeline will run in Offline Mock Mode\n")
            f.write("GEMINI_API_KEY=\n")
        print(f"[INFO] Created template .env file in the project root.")

def display_menu(files: List[str]) -> str:
    """Renders file selection menu."""
    print(f"{BOLD}Discovered Legacy PDF Documents in Workspace:{RESET}")
    for idx, f in enumerate(files, 1):
        size_mb = os.path.getsize(f) / (1024 * 1024)
        print(f"  {BOLD}{idx}.{RESET} {CYAN}{f}{RESET} ({size_mb:.2f} MB)")
    print(f"  {BOLD}E.{RESET} Exit")
    print("-" * 50)
    
    while True:
        choice = input(f"Select a document to ingest (1-{len(files)} or E): ").strip()
        if choice.lower() == 'e':
            print("Exiting pipeline. Goodbye!")
            sys.exit(0)
        try:
            val = int(choice)
            if 1 <= val <= len(files):
                return files[val - 1]
        except ValueError:
            pass
        print(f"{RED}Invalid choice. Please select a valid number or 'E'.{RESET}")

def run_ingestion_progress(file_path: str, vector_store: VectorStore):
    """Simulates a detailed console progress bar for the ingestion steps."""
    print(f"\n[INGESTION] Starting ETL Ingestion Pipeline...")
    
    # 1. Parsing
    print(f"  +- Step 1: Reading PDF layout and extracting pages...")
    start_time = time.time()
    chunks = pipeline.ingest_document(file_path, vector_store)
    duration = time.time() - start_time
    print(f"     [SUCCESS] Loaded {len(chunks)} pages in {duration:.2f}s.")
    
    # 2. Embedding & Vector Storing
    print(f"  +- Step 2: Generating dense vector embeddings...")
    total_steps = 10
    for i in range(1, total_steps + 1):
        percent = int((i / total_steps) * 100)
        bar = "#" * i + "-" * (total_steps - i)
        print(f"\r     Embedding progress: [{bar}] {percent}%", end="", flush=True)
        time.sleep(0.05)
    print()
    print(f"     [SUCCESS] All chunks indexed in Vector Store.")
    print()

def main():
    create_env_template_if_missing()
    render_banner()
    
    # Scan for PDF files in the current folder and data folder for maximum robustness
    pdf_files = []
    
    # 1. Check root directory
    for f in os.listdir("."):
        if f.lower().endswith(".pdf") and os.path.isfile(f):
            pdf_files.append(f)
            
    # 2. Check data directory
    if os.path.exists("data"):
        for f in os.listdir("data"):
            if f.lower().endswith(".pdf"):
                full_path = os.path.join("data", f)
                if os.path.isfile(full_path):
                    pdf_files.append(full_path)
                    
    # Remove duplicates if any
    pdf_files = sorted(list(set(pdf_files)))
    
    if not pdf_files:
        print(f"{RED}[ERROR] No PDF files found in the current folder or data/ folder!{RESET}")
        print("Please place legacy PDF manuals or documents (like sample1.pdf or sample2.pdf) in this directory.")
        return
        
    # Initialize Vector DB
    vector_store = VectorStore()
    
    selected_pdf = display_menu(pdf_files)
    run_ingestion_progress(selected_pdf, vector_store)
    
    while True:
        print("=" * 85)
        print(f"{BOLD}New Requirements Input Phase{RESET}")
        print("Enter the mapping instructions, formatting standards, or new features you want the upgraded V2 document to support.")
        print("Example 1 (For sample1.pdf / US Constitution):")
        print(f"   {YELLOW}\"Extract Article II sections about the President's duties, map them to Executive power and add safety warning about constitutional limits.\" {RESET}")
        print("Example 2 (For sample2.pdf / DHIS2 Manual):")
        print(f"   {YELLOW}\"Extract pivot table creation steps, map them to XYZ dashboard schema, and add a warning limit on query sizes.\" {RESET}")
        print("=" * 85)
        
        query = input(f"{BOLD}New Requirements / Features Query:{RESET}\n> ").strip()
        if not query:
            print(f"{RED}Query cannot be empty. Please try again.{RESET}")
            continue
            
        print(f"\n[RETRIEVAL] Retrieving relevant knowledge chunks from Vector DB...")
        retrieved = pipeline.retrieve_context(query, vector_store, top_k=4)
        
        print(f"\n[FOUND] Retrieved {len(retrieved)} relevant pages:")
        for idx, (score, chunk) in enumerate(retrieved, 1):
            print(f"   {BOLD}{idx}.{RESET} [{chunk['source_file']}] Page {chunk['page_number']} | Similarity Score: {CYAN}{score:.4f}{RESET}")
            snippet = chunk['text'][:150].replace('\n', ' ') + "..."
            print(f"      Snippet: {snippet}")
            
        print(f"\n[GENERATION] Invoking LLM for document reconstruction and enrichment...")
        
        try:
            upgraded_doc: GeneratedDocument = pipeline.generate_upgraded_document(query, retrieved, selected_pdf)
            
            # Save files
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            
            # Save Markdown
            md_content = pipeline.compile_markdown(upgraded_doc)
            with open(OUTPUT_MD, "w", encoding="utf-8") as f:
                f.write(md_content)
                
            # Compile PDF
            pipeline.compile_pdf(upgraded_doc, OUTPUT_PDF)
            
            # Renders results summary
            print("\n" + "=" * 85)
            print(f" {BOLD}{GREEN}UPGRADED DOCUMENT GENERATED SUCCESSFULLY (NEW DOCUMENT V2){RESET} ")
            print("=" * 85)
            print(f"{BOLD}Title:{RESET} {upgraded_doc.title}")
            print(f"{BOLD}Version:{RESET} {upgraded_doc.version}")
            print(f"{BOLD}Overview:{RESET} {upgraded_doc.overview[:180]}...")
            print(f"{BOLD}Sections Created:{RESET} {len(upgraded_doc.sections)}")
            for s in upgraded_doc.sections:
                print(f"  +- {CYAN}{s.heading}{RESET} (Synthesized from page(s): {s.source_pages})")
                
            if upgraded_doc.safety_directives:
                print(f"{BOLD}Safety Directives Enforced:{RESET} {len(upgraded_doc.safety_directives)}")
                for warning in upgraded_doc.safety_directives:
                    print(f"  [WARNING] {warning}")
                    
            if upgraded_doc.faq:
                print(f"{BOLD}Auto-Generated FAQ Pairs:{RESET} {len(upgraded_doc.faq)}")
                for item in upgraded_doc.faq[:2]:
                    print(f"  Q: {item.question}")
                    print(f"  A: {item.answer}")
            
            print("=" * 85)
            print(f"{BOLD}Output Files Saved:{RESET}")
            print(f"  - Markdown: {GREEN}{OUTPUT_MD}{RESET}")
            print(f"  - PDF Copy: {GREEN}{OUTPUT_PDF}{RESET}")
            print("=" * 85)
            
        except Exception as e:
            print(f"\n{RED}[ERROR] Pipeline failed during generation/validation: {e}{RESET}")
            import traceback
            traceback.print_exc()
            
        print()
        cont = input("Do you want to run another query on this document? (Y/N): ").strip().lower()
        if cont != 'y':
            break

    print("Exiting pipeline. Goodbye!")

if __name__ == "__main__":
    main()
