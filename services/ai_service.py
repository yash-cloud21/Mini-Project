import os
import re
import json
from flask import current_app
from database.db import get_db

# Try importing the AI library
try:
    import warnings
    warnings.filterwarnings("ignore", category=FutureWarning, module="google.generativeai")
    
    import google.generativeai as genai
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False


def _scrub_pii(text):
    """
    Remove common Personally Identifiable Information (PII) from text 
    before sending it to the external LLM.
    """
    if not text:
        return text
        
    # Remove Email addresses
    text = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '[EMAIL REMOVED]', text)
    
    # Remove Phone numbers (generic formats)
    text = re.sub(r'(\+\d{1,2}\s?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}', '[PHONE REMOVED]', text)
    
    # Remove URLs/Links (often pointing to personal portfolios/linkedins)
    text = re.sub(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+', '[URL REMOVED]', text)
    
    return text

def _get_cached_insight(user_id, context_type):
    """Fetch insight from cache if it exists."""
    db = get_db()
    cache = db.execute(
        "SELECT insight_text, source FROM ai_insights_cache WHERE user_id = ? AND context_type = ? ORDER BY generated_at DESC LIMIT 1",
        (user_id, context_type)
    ).fetchone()
    
    if cache:
        return {
            'source': cache['source'],
            'text': cache['insight_text']
        }
    return None

def _cache_insight(user_id, context_type, text, source):
    """Store generated insight into the cache."""
    db = get_db()
    
    # Simple overwrite strategy: delete old, insert new
    db.execute("DELETE FROM ai_insights_cache WHERE user_id = ? AND context_type = ?", (user_id, context_type))
    
    db.execute(
        "INSERT INTO ai_insights_cache (user_id, context_type, insight_text, source) VALUES (?, ?, ?, ?)",
        (user_id, context_type, text, source)
    )
    db.commit()

import concurrent.futures

def _call_gemini_with_timeout(prompt, timeout_seconds=10):
    """
    Wrap the Gemini call to ensure it has a strict timeout and handles errors gracefully.
    """
    api_key = current_app.config.get('GEMINI_API_KEY')
    if not AI_AVAILABLE or not api_key:
        raise ValueError("AI API not configured or library missing.")
        
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    def _make_call():
        response = model.generate_content(prompt)
        return response.text

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_make_call)
            # This will raise TimeoutError if it takes longer than timeout_seconds
            return future.result(timeout=timeout_seconds)
    except concurrent.futures.TimeoutError:
        print("Gemini API Error: Request timed out.")
        raise TimeoutError("The AI request timed out.")
    except Exception as e:
        print(f"Gemini API Error: {str(e)}")
        raise e


def generate_profile_insights(user_id, acad_data, coding_data, career_data, force_refresh=False):
    """
    Generate personalized learning recommendations based on the unified profile.
    """
    context_type = 'dashboard_insights'
    
    if not force_refresh:
        cached = _get_cached_insight(user_id, context_type)
        if cached:
            return cached
            
    # Compile the prompt data
    prompt = f"""
    You are an AI career advisor for a computer science student.
    Review the student's current profile summary and provide 3-4 bullet points of encouraging, actionable advice on what they should focus on next to improve their readiness for their target role.
    Keep the response under 150 words. Format as Markdown.
    
    Academic Data: Avg Attendance: {acad_data.get('avg_attendance', 'N/A')}%.
    Coding Data: Solved {coding_data.get('solved', 0)} out of {coding_data.get('total', 0)} problems.
    Career Target: {career_data.get('target_role', {}).get('title', 'None Selected')}.
    Missing Skills for Target Role: {', '.join(career_data.get('missing_skills', []))}
    """
    
    try:
        # Note: In a real app we'd enforce the 10s timeout tightly here.
        ai_response = _call_gemini_with_timeout(prompt)
        result = {'source': 'ai', 'text': ai_response}
    except Exception:
        # Fallback logic
        fallback_text = "### Rule-based Recommendations\n"
        
        if acad_data.get('avg_attendance', 100) < 75:
            fallback_text += "- **Academics**: Your attendance is dropping. Try to attend more classes to keep up with the coursework.\n"
            
        if coding_data.get('solved', 0) == 0:
            fallback_text += "- **Coding**: You haven't solved any coding problems yet. Start with the 'easy' ones in the Arrays topic.\n"
        elif coding_data.get('solve_rate', 0) < 50:
            fallback_text += "- **Coding**: Keep practicing! Try solving one problem every day to improve your success rate.\n"
            
        if career_data.get('status') == 'success' and career_data.get('missing_skills'):
            fallback_text += f"- **Career**: Focus on learning these missing skills: {', '.join(career_data['missing_skills'][:3])}.\n"
        elif career_data.get('status') != 'success':
            fallback_text += "- **Career**: Select a target job role in the Career section to get skill recommendations.\n"
            
        if fallback_text == "### Rule-based Recommendations\n":
            fallback_text += "You are doing great across academics, coding, and career prep. Keep up the good work!"
            
        result = {'source': 'fallback', 'text': fallback_text}
        
    _cache_insight(user_id, context_type, result['text'], result['source'])
    return result


def generate_resume_feedback(user_id, resume_text, target_role_name, force_refresh=False):
    """
    Generate NLP-based improvement suggestions for a resume against a target role.
    """
    context_type = f'resume_feedback_{target_role_name.replace(" ", "_")}'
    
    if not force_refresh:
        cached = _get_cached_insight(user_id, context_type)
        if cached:
            return cached
            
    scrubbed_text = _scrub_pii(resume_text)
    
    prompt = f"""
    You are an expert technical recruiter. Review the following student resume text and suggest 3 specific, actionable improvements to make it stronger for a '{target_role_name}' position.
    Do NOT rewrite the resume. Provide 3 short bullet points. Format as Markdown.
    
    RESUME TEXT:
    {scrubbed_text[:3000]} # Limit length for token limits
    """
    
    try:
        ai_response = _call_gemini_with_timeout(prompt)
        result = {'source': 'ai', 'text': ai_response}
    except Exception:
        fallback_text = f"### General Resume Tips for {target_role_name}\n"
        fallback_text += "- Ensure your most relevant projects are listed at the top.\n"
        fallback_text += "- Use action verbs (e.g., 'Developed', 'Optimized') to describe your experience.\n"
        fallback_text += f"- Make sure your skills section clearly highlights technologies relevant to a {target_role_name}."
        result = {'source': 'fallback', 'text': fallback_text}
        
    _cache_insight(user_id, context_type, result['text'], result['source'])
    return result
