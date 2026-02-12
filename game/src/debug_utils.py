"""
Debug utilities for game development.
Provides human-readable output of LLM interactions.
"""
import textwrap
from typing import List
from llm import LLMMessage, LLMFunction


def wrap_text(text: str, width: int = 80, indent: str = "") -> str:
    """
    Wrap text to specified width with optional indentation.
    
    Args:
        text: Text to wrap
        width: Maximum line width
        indent: String to prepend to each line
        
    Returns:
        Wrapped text
    """
    # Handle empty text
    if not text:
        return indent + "(empty)"
    
    # Preserve paragraph breaks
    paragraphs = text.split('\n')
    wrapped_paragraphs = []
    
    for para in paragraphs:
        if para.strip():
            wrapped = textwrap.fill(
                para,
                width=width,
                initial_indent=indent,
                subsequent_indent=indent,
                break_long_words=False,
                break_on_hyphens=False
            )
            wrapped_paragraphs.append(wrapped)
        else:
            wrapped_paragraphs.append("")  # Preserve empty lines
    
    return '\n'.join(wrapped_paragraphs)


def format_function(func: LLMFunction, indent: str = "  ") -> str:
    """
    Format a function for display.
    
    Args:
        func: LLMFunction to format
        indent: Indentation string
        
    Returns:
        Formatted function string
    """
    output = f"{indent}• {func.name}\n"
    if func.description:
        desc = wrap_text(func.description, width=76, indent=f"{indent}  ")
        output += f"{desc}\n"
    return output


def print_llm_debug(
    messages: List[LLMMessage],
    functions: List[LLMFunction],
    title: str = "LLM REQUEST"
) -> None:
    """
    Print LLM request in human-readable format.
    
    Args:
        messages: List of LLM messages (including system prompt)
        functions: Available functions
        title: Title for the debug output
    """
    width = 80
    divider = "=" * width
    section_divider = "-" * width
    
    print("\n" + divider)
    print(f" {title}".center(width))
    print(divider)
    
    # Separate system prompt from conversation
    system_messages = [m for m in messages if m.role == "system"]
    conversation_messages = [m for m in messages if m.role != "system"]
    
    # Print system prompt
    if system_messages:
        print("\n" + section_divider)
        print("SYSTEM PROMPT")
        print(section_divider)
        for msg in system_messages:
            print(wrap_text(msg.content, width=width))
    
    # Print available functions (always show, with indicator for delivery method)
    if functions:
        # Check if functions are embedded in system prompt (JSON-based approach)
        functions_in_prompt = any("VERFÜGBARE FUNKTIONEN:" in msg.content for msg in system_messages)
        delivery_method = "JSON parsing" if functions_in_prompt else "native function API"

        print("\n" + section_divider)
        print(f"AVAILABLE FUNCTIONS ({delivery_method}) — {len(functions)}")
        print(section_divider)
        for func in functions:
            print(format_function(func))
    
    # Print conversation history
    if conversation_messages:
        print("\n" + section_divider)
        print("CONVERSATION HISTORY")
        print(section_divider)
        
        for i, msg in enumerate(conversation_messages, 1):
            role_label = "USER" if msg.role == "user" else "ASSISTANT"
            print(f"\n[{role_label} #{i}]")
            print(wrap_text(msg.content, width=width, indent="  "))
    
    print("\n" + divider + "\n")


def print_llm_response(
    response_text: str,
    function_call: str = None,
    function_success: bool = True
) -> None:
    """
    Print LLM response in human-readable format.
    
    Args:
        response_text: The response text from LLM
        function_call: Name of function called (if any)
        function_success: Whether function execution succeeded
    """
    width = 80
    divider = "=" * width
    
    print("\n" + divider)
    print(" LLM RESPONSE".center(width))
    print(divider)
    
    print("\n[NARRATIVE RESPONSE]")
    print(wrap_text(response_text, width=width, indent="  "))
    
    if function_call:
        status = "✓ SUCCESS" if function_success else "✗ FAILED"
        print(f"\n[FUNCTION CALL: {function_call}] {status}")
    else:
        print("\n[FUNCTION CALL: None]")
    
    print("\n" + divider + "\n")


def print_history_summary(history) -> None:
    """
    Print a summary of the game history.
    
    Args:
        history: GameHistory object
    """
    width = 80
    divider = "=" * width
    
    print("\n" + divider)
    print(" GAME HISTORY SUMMARY".center(width))
    print(divider)
    
    if not history.entries:
        print("\n  (No history entries)")
        print("\n" + divider + "\n")
        return
    
    print(f"\n  Total Turns: {history.turn_counter}")
    print(f"  Stored Entries: {len(history.entries)}")
    print(f"  Max Length: {history.max_length}")
    
    print("\n  Recent Turns:")
    for entry in history.entries[-5:]:  # Show last 5
        user_preview = entry.user_input[:40] + "..." if len(entry.user_input) > 40 else entry.user_input
        func_info = f" → {entry.chosen_function}" if entry.chosen_function else ""
        print(f"    Turn {entry.turn_number}: {user_preview}{func_info}")
    
    print("\n" + divider + "\n")