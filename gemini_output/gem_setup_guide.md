# How to Create Your Gemini Gem

Gemini Gems are custom AI personas that remember your context across all conversations.

## Requirements
- Gemini Advanced subscription (required for Gems)

## Step 1: Open Gem Manager
1. Go to https://gemini.google.com
2. Look for the **Gem Manager** in the left sidebar
3. Click **"New Gem"**

## Step 2: Configure Your Gem

### Name
```
My Dev Partner
```
(or choose your own name)

### Description
Copy from `gem_description.txt` or use:
```
Personal dev partner with expertise in JavaScript, Ruby, TypeScript, sql Knows 687+ projects including Carvis Agent Guideline, Carvis Service Recommendations Review Imported from ChatGPT history.
```

### Instructions
Copy the entire contents of `gemini_gem_instructions.txt` and paste it into the Instructions field.

## Step 3: Optional - Add Knowledge Files
You can upload `context_pack.json` to the Knowledge section for the Gem to reference detailed project information.

## Step 4: Save and Test
1. Click **Save**
2. Open your new Gem from the sidebar
3. Test with questions like:
   - "What projects am I working on?"
   - "What's my tech stack?"
   - "Help me with my Carvis project"

## Tips
- The Gem persists across sessions - no need to re-paste context
- You can create multiple Gems for different purposes (work, personal, specific projects)
- Edit the Instructions anytime to update your context

## Updating Your Gem
When you export new conversations, re-run the export and update the Instructions field with the new content.