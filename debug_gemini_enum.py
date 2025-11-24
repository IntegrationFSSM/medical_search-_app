
import google.generativeai as genai
from google.generativeai.types import FinishReason

print("FinishReason Enum:")
for member in FinishReason:
    print(f"{member.name}: {member.value}")
