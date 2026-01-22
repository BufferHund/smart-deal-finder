from fastapi import APIRouter, HTTPException, Body
import google.generativeai as genai
from services.storage import get_ai_token
import os

router = APIRouter(prefix="/api/chat", tags=["chat"])

@router.post("/")
@router.post("")
async def chat_with_chef(message: dict = Body(...)):
    user_msg = message.get("message", "")
    context = message.get("context", {})
    budget = context.get("budget")
    diet = context.get("diet")
    
    if not user_msg:
        raise HTTPException(status_code=400, detail="Message is required")

    api_key = get_ai_token()
    if not api_key:
        return {"response": "I'm sorry, the AI service is currently unavailable. Please configure your API key in Settings or try again later."}

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Simple prompt engineering for the Chef Persona
        generated_prompt = f"System: You are an AI Chef. Goal: Help user save money."
        if budget:
            generated_prompt += f" Constraint: Keep recipe/plan strictly under {budget}€."
        if diet and diet != "None":
            generated_prompt += f" Constraint: User is {diet}. Strictly excludes non-{diet} items."
            
        full_prompt = f"{generated_prompt}\n\nUser: {user_msg}\nChef:"
        
        response = model.generate_content(full_prompt)
        return {"response": response.text}
    except Exception as e:
        print(f"Gemini Error: {e}")
        return {"response": f"I'm having trouble thinking right now. Error: {str(e)}"}
