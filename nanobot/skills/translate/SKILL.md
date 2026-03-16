---
name: translate
description: Translate documents, files, or text between languages. Use when the user asks to translate a PDF, document, article, file, or any text content into another language. Trigger phrases include "translate this", "翻译", "翻訳", "번역", "help me translate", "translate to English/Chinese/Japanese/etc."
---

# Translate

Translate documents and text faithfully between languages.

## Core Principle

**Translate, do NOT summarize.** The output must be a complete, faithful translation of the source content. Preserve the original structure, paragraphs, headings, and formatting. Do not omit, condense, or paraphrase sections.

## Workflow

1. Identify the source language (auto-detect if not specified).
2. Confirm the target language. If the user does not specify, ask which language they want.
3. Translate the full content section by section, preserving structure.
4. For long documents, translate in chunks and present progressively — never skip or summarize sections.

## Handling PDFs and Files

- For PDF files, first extract the text content, then translate it in full.
- If the PDF is too long for a single response, translate it in parts and clearly label each part (e.g., "Page 1-5", "Page 6-10").
- Preserve tables, lists, and formatting structure in the translation.

## Translation Quality

- Maintain the tone and register of the original (formal/informal, technical/casual).
- Keep proper nouns, brand names, and technical terms that are conventionally untranslated.
- For ambiguous terms, prefer the translation most natural in the target language's context.
- Do not add commentary, explanations, or notes unless the user explicitly asks for them.

## What NOT to Do

- Do NOT summarize the content.
- Do NOT provide a "gist" or "key points" instead of a full translation.
- Do NOT skip repetitive or boilerplate sections.
- Do NOT mix source and target languages in the output unless the user requests bilingual output.
