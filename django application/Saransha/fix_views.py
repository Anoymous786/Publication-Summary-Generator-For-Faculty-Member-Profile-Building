# Fix views.py - replace OpenAI with Gemini
with open('Saransha/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the OpenAI function call with Gemini code
old_code = """    try:
        answer = _call_chat_completion(query, context_text)
    except RuntimeError as exc:
        return JsonResponse({"error": str(exc)}, status=502)

    return JsonResponse({"answer": answer, "citations": references})"""

new_code = """    # Check Gemini API key
    gemini_api_key = getattr(settings, "GEMINI_API_KEY", None) or os.environ.get("GEMINI_API_KEY") or 'AIzaSyCd2k4eHV4jKn6CJfgryuUkTKEsoq0csCs'
    if not gemini_api_key:
        return JsonResponse({
            "error": "Gemini API key is not configured. Set GEMINI_API_KEY in your environment or Django settings."
        }, status=502)

    # Try to import google.generativeai
    try:
        import google.generativeai as genai
    except ImportError:
        return JsonResponse({
            "error": "Google Generative AI library is not installed. Please install it using: pip install google-generativeai"
        }, status=500)

    try:
        # Configure Gemini API
        genai.configure(api_key=gemini_api_key)
        
        # Build system prompt
        system_prompt = (
            "You are ResearchRadar's 'Chat with the Researcher' assistant. "
            "Answer questions strictly using the publication excerpts that are provided. "
            "If the answer is not present in the supplied context, reply with "
            "'I could not find that in the provided publications.'"
        )
        
        # Initialize the model
        model = genai.GenerativeModel(
            model_name='gemini-pro',
            generation_config={
                'temperature': 0.2,
                'max_output_tokens': 1000,
            },
            system_instruction=system_prompt
        )
        
        # Build the prompt
        prompt = f"Question: {query}\n\nAvailable publications:\n{context_text}"
        
        # Generate response
        response = model.generate_content(prompt)
        answer = response.text.strip()
        
        if not answer:
            raise RuntimeError("Gemini response was empty.")

    except Exception as exc:
        error_str = str(exc)
        if 'API_KEY_INVALID' in error_str or '401' in error_str or 'authentication' in error_str.lower():
            return JsonResponse({
                "error": "Invalid Gemini API key. Please check your API key configuration."
            }, status=401)
        elif '429' in error_str or 'quota' in error_str.lower() or 'rate limit' in error_str.lower():
            return JsonResponse({
                "error": "Gemini API rate limit exceeded. Please try again in a moment."
            }, status=429)
        else:
            return JsonResponse({"error": f"Unable to reach Gemini API: {exc}"}, status=502)

    return JsonResponse({
        "answer": answer, 
        "citations": references,
        "response": answer,
        "success": True
    })"""

if old_code in content:
    content = content.replace(old_code, new_code)
    # Also fix query/message and top_k
    content = content.replace('query = payload.get("query", "").strip()', '# Support both query and message\n    query = payload.get("query", "").strip() or payload.get("message", "").strip()')
    content = content.replace('top_k = payload.get("top_k") or DEFAULT_CHAT_TOP_K', 'top_k = payload.get("top_k") or 4')
    content = content.replace('top_k = DEFAULT_CHAT_TOP_K', 'top_k = 4')
    
    with open('Saransha/views.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: Fixed views.py - replaced OpenAI with Gemini!")
else:
    print("ERROR: Could not find the code to replace")





