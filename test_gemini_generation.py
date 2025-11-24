
import os
import django
from django.conf import settings
import sys

# Setup Django environment
sys.path.append('c:\\Users\\yassi\\medical_search_app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medical_search.settings')
django.setup()

from pathology_search.services import PathologySearchService

def test_gemini_generation():
    print("🧪 Testing Gemini Generation...")
    
    # Check API Key
    if not settings.GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY not found in settings!")
        return

    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.GEMINI_API_KEY)
        
        # print("📋 Listing available Gemini models:")
        # for m in genai.list_models():
        #     if 'generateContent' in m.supported_generation_methods:
        #         print(f"  - {m.name}")
        
        # Initialize service with Gemini model
        service = PathologySearchService(model='gemini-2.5-pro')
        
        # Dummy data
        pathology_name = "Trouble Dépressif Majeur"
        form_data = {
            "Humeur": ["Tristesse", "Perte d'intérêt"],
            "Physique": ["Fatigue", "Insomnie"]
        }
        similarity_score = 85.5
        medical_text = "Le trouble dépressif majeur est caractérisé par..."
        
        # Call generation
        print("🔄 Calling generate_ai_diagnosis...")
        result = service.generate_ai_diagnosis(
            pathology_name=pathology_name,
            form_data=form_data,
            similarity_score=similarity_score,
            medical_text=medical_text
        )
        
        if result['success']:
            print("✅ Generation Successful!")
            print(f"📄 Treatment Plan Length: {len(result['treatment_plan'])} chars")
            print("📝 Preview:")
            print(result['treatment_plan'][:200] + "...")
        else:
            print(f"❌ Generation Failed: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ Exception during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_gemini_generation()
