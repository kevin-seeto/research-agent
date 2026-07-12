# post_now.py - Review and post LinkedIn draft
import os, glob
from dotenv import load_dotenv
load_dotenv()

# Show all available drafts
drafts = sorted(glob.glob("drafts/linkedin_draft_*.txt"), reverse=True)

if not drafts:
    print("No drafts found. Run agent.py first.")
    exit()

print("\nAvailable drafts:")
for i, d in enumerate(drafts):
    print(str(i+1) + ". " + d)

choice = input("\nWhich draft to post? (enter number): ")
filename = drafts[int(choice)-1]

# Read full draft
with open(filename, "r") as f:
    full_content = f.read()

# Extract just the LinkedIn post section
if "=== LINKEDIN POST" in full_content:
    linkedin_section = full_content.split("=== LINKEDIN POST")[1]
    # Skip the header lines
    lines = linkedin_section.strip().split("\n")
    # Skip first 2 header lines and get the post
    post_text = "\n".join(lines[2:]).strip()
else:
    post_text = full_content

# Show full briefing first
print("\n--- FULL RESEARCH BRIEFING ---")
if "=== FULL RESEARCH BRIEFING ===" in full_content:
    briefing_section = full_content.split("==================================================")[0]
    print(briefing_section)
print("--- END BRIEFING ---\n")

# Show LinkedIn post preview
print("--- LINKEDIN POST PREVIEW ---")
print(post_text)
print("--- END PREVIEW ---")
print("\nCharacter count: " + str(len(post_text)) + " of 2800 limit")

# Confirm
confirm = input("\nPost this to LinkedIn? (yes/no): ")

if confirm.lower() == "yes":
    from agent import post_to_linkedin
    status = post_to_linkedin(post_text)
    print(status)
elif confirm.lower() == "no":
    print("\nPost cancelled.")
    print("Tip: Edit the LinkedIn post section in " + filename + " then run post_now.py again.")
else:
    print("Invalid input - type yes or no.")