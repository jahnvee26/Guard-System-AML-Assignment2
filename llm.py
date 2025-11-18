"""
LLM Module for Conversational Intruder Detection
Handles conversations with unknown intruders using a language model.
"""

import os
import threading
import queue
import time
from typing import Optional, List, Dict

try:
    from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("Warning: transformers not available. LLM features will be limited.")


class IntruderConversationManager:
    """
    Manages conversations with intruders using an LLM.
    """
    
    def __init__(self, model_name: str = "facebook/opt-125m"):
        """
        Initialize the conversation manager.
        
        Args:
            model_name: The huggingface model to use for conversation.
                       Default is a small model that can run on CPU.
        """
        self.conversation_active = False
        self.conversation_history: List[Dict[str, str]] = []
        self.response_queue = queue.Queue()
        self.model_name = model_name
        self.generator = None
        
        # System prompt for the intruder conversation
        self.system_prompt = """You are a security AI assistant. An unknown person has been detected in a restricted area. 
Your goal is to:
1. Identify who they are and why they're there
2. Determine if they have authorization
3. Keep them engaged while security is notified
4. Be professional but firm

Keep responses SHORT (1-2 sentences max) and conversational. Be direct and clear."""
        
        self._initialize_model()
    
    def _initialize_model(self):
        """
        Initialize the LLM model.
        """
        if not TRANSFORMERS_AVAILABLE:
            print("LLM: Transformers not available. Using fallback responses.")
            return
        
        try:
            print(f"LLM: Loading model '{self.model_name}'...")
            # Use a smaller, faster model for real-time conversation
            self.generator = pipeline(
                'text-generation',
                model=self.model_name,
                device=-1,  # CPU
                max_length=150,
                do_sample=True,
                temperature=0.7,
                top_p=0.9
            )
            print("LLM: Model loaded successfully!")
        except Exception as e:
            print(f"LLM: Error loading model: {e}")
            print("LLM: Falling back to rule-based responses.")
            self.generator = None
    
    def _get_fallback_response(self, intruder_text: str) -> str:
        """
        Get a fallback response when LLM is not available.
        Uses rule-based logic.
        """
        intruder_lower = intruder_text.lower()
        
        # Check conversation turn count
        turn_count = len([m for m in self.conversation_history if m['role'] == 'intruder'])
        
        if turn_count == 0:
            return "Hello, I've detected your presence. Can you please identify yourself?"
        
        # Check for greetings
        if any(word in intruder_lower for word in ['hello', 'hi', 'hey']):
            return "Hello. This is a restricted area. Who are you and why are you here?"
        
        # Check for identification attempts
        if any(word in intruder_lower for word in ['name is', 'i am', "i'm", 'my name']):
            return "I see. Do you have authorization to be in this area? Can you provide a code or badge number?"
        
        # Check for authorization claims
        if any(word in intruder_lower for word in ['authorized', 'permission', 'allowed', 'badge']):
            return "Please wait here while I verify your credentials. Security has been notified."
        
        # Check for hostility or refusal
        if any(word in intruder_lower for word in ['no', 'none', 'leave me', 'mind your']):
            return "I must inform you that this area is under surveillance. Please comply or leave immediately."
        
        # Check for confusion
        if any(word in intruder_lower for word in ['what', 'where', 'who', 'confused', 'lost']):
            return "You are in a restricted area. If you are lost, please leave the way you came and contact security."
        
        # Default responses based on turn count
        responses = [
            "I need you to identify yourself. Who are you?",
            "This area is under surveillance. Why are you here?",
            "Please state your purpose for being in this location.",
            "Security has been alerted. Please remain where you are.",
            "I'm waiting for your response. Why are you in this restricted area?"
        ]
        
        return responses[min(turn_count - 1, len(responses) - 1)]
    
    def _generate_response(self, intruder_text: str) -> str:
        """
        Generate a response to the intruder using the LLM or fallback logic.
        
        Args:
            intruder_text: What the intruder said
            
        Returns:
            The AI's response
        """
        # Add intruder's message to history
        self.conversation_history.append({
            'role': 'intruder',
            'content': intruder_text
        })
        
        # Use fallback if model not available
        if self.generator is None:
            response = self._get_fallback_response(intruder_text)
        else:
            try:
                # Build conversation context
                conversation_text = self.system_prompt + "\n\n"
                for msg in self.conversation_history[-6:]:  # Last 3 exchanges
                    if msg['role'] == 'intruder':
                        conversation_text += f"Intruder: {msg['content']}\n"
                    else:
                        conversation_text += f"Security AI: {msg['content']}\n"
                conversation_text += "Security AI:"
                
                # Generate response
                outputs = self.generator(
                    conversation_text,
                    max_new_tokens=50,
                    num_return_sequences=1,
                    pad_token_id=self.generator.tokenizer.eos_token_id
                )
                
                # Extract the response
                full_response = outputs[0]['generated_text']
                response = full_response.split("Security AI:")[-1].strip()
                
                # Clean up the response
                response = response.split('\n')[0].strip()
                
                # If response is empty or too long, use fallback
                if not response or len(response) > 200:
                    response = self._get_fallback_response(intruder_text)
                    
            except Exception as e:
                print(f"LLM: Error generating response: {e}")
                response = self._get_fallback_response(intruder_text)
        
        # Add AI's response to history
        self.conversation_history.append({
            'role': 'assistant',
            'content': response
        })
        
        return response
    
    def start_conversation(self) -> str:
        """
        Start a new conversation with an intruder.
        
        Returns:
            The opening message from the AI
        """
        self.conversation_active = True
        self.conversation_history = []
        
        # Initial greeting/warning
        opening = "Attention! I have detected an unknown person. Please identify yourself immediately."
        
        self.conversation_history.append({
            'role': 'assistant',
            'content': opening
        })
        
        print(f"LLM: Started conversation with intruder")
        return opening
    
    def process_intruder_response(self, intruder_text: str) -> str:
        """
        Process the intruder's response and generate an AI reply.
        
        Args:
            intruder_text: What the intruder said
            
        Returns:
            The AI's response
        """
        if not self.conversation_active:
            return self.start_conversation()
        
        print(f"LLM: Processing intruder response: '{intruder_text}'")
        response = self._generate_response(intruder_text)
        print(f"LLM: Generated response: '{response}'")
        
        return response
    
    def end_conversation(self):
        """
        End the current conversation.
        """
        self.conversation_active = False
        print(f"LLM: Ended conversation (Total exchanges: {len(self.conversation_history) // 2})")
    
    def is_conversation_active(self) -> bool:
        """
        Check if a conversation is currently active.
        """
        return self.conversation_active
    
    def get_conversation_summary(self) -> str:
        """
        Get a summary of the conversation.
        """
        if not self.conversation_history:
            return "No conversation history."
        
        summary = "Conversation Summary:\n"
        for i, msg in enumerate(self.conversation_history, 1):
            role = "Security AI" if msg['role'] == 'assistant' else "Intruder"
            summary += f"{i}. {role}: {msg['content']}\n"
        
        return summary


if __name__ == "__main__":
    print("=== LLM Conversation Module Test ===\n")
    
    # Test the conversation manager
    manager = IntruderConversationManager()
    
    print("\nTest 1: Starting conversation")
    opening = manager.start_conversation()
    print(f"AI: {opening}")
    
    print("\nTest 2: Simulating intruder responses")
    test_responses = [
        "Who are you?",
        "I'm John, I work here.",
        "I have a badge somewhere...",
    ]
    
    for response in test_responses:
        print(f"\nIntruder: {response}")
        ai_response = manager.process_intruder_response(response)
        print(f"AI: {ai_response}")
    
    print("\n" + "="*50)
    print(manager.get_conversation_summary())
    
    manager.end_conversation()
    print("\nTest complete!")
