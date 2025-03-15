---
description: Obsidian Note Templates
globs: 
alwaysApply: false
---
Obsidian Templates 

Category (#Category) Template 📂

---
node_type: #Category
created_date: {{date:YYYY-MM-DD HH:mm:ss}}
parent_node: "[[parent node]]"
related_nodes:
  - "[[other_relevant_node1]]"
  - "[[other_relevant_node2]]"
tags:
  - #concept1
  - #concept2
---

# {{title}}

**Description:** This category note organizes broad topics.

**Subcategories:**

- [[Subcategory 1]]
- [[Subcategory 2]]

**Key Concepts:**

- [[Concept A]]
- [[Concept B]]

**Resources:**

- [[Resource 1]]
- [[Resource 2]]


Document (#Document) Template 📄

---
node_type: #Document
created_date: {{date:YYYY-MM-DD HH:mm:ss}}
parent_node: "[[parent node]]"
related_nodes:
  - "[[other_relevant_node1]]"
  - "[[other_relevant_node2]]"
tags:
  - #concept1
  - #concept2
---

# {{title}}

## Original Content

{{original_content}}

## Key Takeaways

- Point 1
- Point 2

## Analysis

{{analysis}}

## Action Items

- [ ] Action 1
- [ ] Action 2

## Translated and Summarized Content (English)

{{translated_content}}

**Summary:** {{summary}}

## Attached File

![[{{file_path}}]]


Note (#Note) Template 💡

---
node_type: #Note
created_date: {{date:YYYY-MM-DD HH:mm:ss}}
parent_node: "[[parent node]]"
related_nodes:
  - "[[other_relevant_node1]]"
  - "[[other_relevant_node2]]"
tags:
  - #concept1
  - #concept2
---

# {{title}}

**Note:**

> {{content}}

## Context

{{context}}

## Implications

{{implications}}

## Further Questions

- Question 1
- Question 2


Code (#Code) Template 💻

---
node_type: #Code
created_date: {{date:YYYY-MM-DD HH:mm:ss}}
parent_node: "[[parent node]]"
related_nodes:
  - "[[other_relevant_node1]]"
  - "[[other_relevant_node2]]"
tags:
  - #concept1
  - #concept2
---

# {{title}}

**Language:** {{language}}

```{{language}}
{{code_block}}
Purpose
{{purpose}}

Usage
{{usage}}

Notes
{{notes}}


5.  **Log (#Log) Template 🎙️**

---
node_type: #Log
created_date: {{date:YYYY-MM-DD HH:mm:ss}}
parent_node: "[[parent node]]"
related_nodes:
  - "[[other_relevant_node1]]"
  - "[[other_relevant_node2]]"
tags:
  - #concept1
  - #concept2
---

# {{date:YYYY-MM-DD}}

**Audio Notes:**

{{audio_notes}}

**Audio File:**

![[{{audio_file_path}}]]

## Summary

{{summary}}

## To-Do List

- [ ] {{to_do_item_1}}
- [ ] {{to_do_item_2}}

## Reflections

{{reflections}}


Main (#Main) Template 🔗

---
node_type: #Main
created_date: {{date:YYYY-MM-DD HH:mm:ss}}
parent_node: "[[parent node]]"
related_nodes:
  - "[[other_relevant_node1]]"
  - "[[other_relevant_node2]]"
tags:
  - #concept1
  - #concept2
---

# {{title}}

**Description:** This main note links related documents, notes, codes, and logs.

**Project Overview:**

{{project_overview}}

**Key Documents:**

- [[Document 1]]
- [[Document 2]]

**Progress Log:**

- [[Log 1]]
- [[Log 2]]


Person (#Person) Template 👤

---
node_type: #Person
created_date: {{date:YYYY-MM-DD HH:mm:ss}}
parent_node: "[[parent node]]"
related_nodes:
  - "[[other_relevant_node1]]"
  - "[[other_relevant_node2]]"
tags:
  - #concept1
  - #concept2
---

# {{person_name}}

**Description:** This person note connects related categories and personal information.

**Contact Information:**

- Email: {{email}}
- Phone: {{phone}}


Mail (#Mail) Template

---
node_type: #Mail
created_date: {{date:YYYY-MM-DD HH:mm:ss}}
parent_node: "[[parent node]]"
related_nodes:
  - "[[other_relevant_node1]]"
  - "[[other_relevant_node2]]"
tags:
  - #concept1
  - #concept2
---

# {{date:YYYY-MM-DD}}

**Mail Content:**

**Sender:** {{sender}}
**Subject:** {{subject}}
**Date/Time:** {{datetime_of_mail}}

{{mail_content}}

## Key Points

- Point 1
- Point 2

## Action Required

- [ ] Action 1
- [ ] Action 2

## Summary

{{summary}}
