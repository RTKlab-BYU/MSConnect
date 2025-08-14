"""
Define the app pages for the project.
"""

# === Standard library imports ===
import os
import time
import pickle

# === Django imports ===
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.shortcuts import render

# === Local imports ===
from .worklist_processor import generate_worklist

# === Constants ===
UPLOAD_DIR = os.path.join(settings.BASE_DIR, 'uploads')
CACHE_FILE = os.path.join(settings.BASE_DIR, 'cache', 'worklist_cache.pkl')
TEMPLATE_FILE = os.path.join(settings.BASE_DIR, 'file_manager', 'files', 'worklist_template.xlsx')

# === Views ===

@login_required
def worklist_view(request):
    """
    Upload an Excel file and generate worklist CSVs.
    """
    context = {
        "facility_name": "My Facility",  # Replace or pull from DB/settings
        "upload_success": None,
        "upload_error": None,
        "csv1_ready": False,
        "csv2_ready": False,
        "csv1_url": None,
        "csv2_url": None,
    }

    # Load cached results if available
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'rb') as handle:
            cached_data = pickle.load(handle)
            cached_data["last_updated"] = time.ctime(os.path.getctime(CACHE_FILE))
            context.update(cached_data)

    # Handle form submission
    if request.method == "POST" and request.FILES.get("excel_file"):
        uploaded_file = request.FILES["excel_file"]
        try:
            os.makedirs(UPLOAD_DIR, exist_ok=True)
            input_path = os.path.join(UPLOAD_DIR, uploaded_file.name)

            # Save uploaded file to disk
            with open(input_path, 'wb+') as f:
                for chunk in uploaded_file.chunks():
                    f.write(chunk)

            # Process file
            csv1_path, csv2_path = generate_worklist(input_path)

            # Save file paths in session for download
            request.session['csv1_path'] = csv1_path
            request.session['csv2_path'] = csv2_path

            context["upload_success"] = "File uploaded and processed successfully."
            context["csv1_ready"] = True
            context["csv2_ready"] = True

        except Exception as e:
            context["upload_error"] = f"Upload failed: {str(e)}"

    return render(request, "worklist/worklist.html", context)


@login_required
def download_template_excel(request):
    """
    Download the Excel template file.
    """
    if os.path.exists(TEMPLATE_FILE):
        return FileResponse(open(TEMPLATE_FILE, 'rb'), as_attachment=True, filename='worklist_template.xlsx')
    else:
        raise Http404("Template file not found")


@login_required
def download_csv(request, which):
    """
    Download the generated CSV files (MS or LC).
    """
    rel_path = request.session.get(f"{which}_path")
    if not rel_path:
        raise Http404(f"{which} file not available in session.")

    abs_path = os.path.join(settings.BASE_DIR, rel_path)

    if not os.path.exists(abs_path):
        return HttpResponse(f"File not found on disk at {abs_path}", status=404)

    return FileResponse(open(abs_path, 'rb'), as_attachment=True, filename=os.path.basename(abs_path))
