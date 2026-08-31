#!/bin/bash
# Search GitHub for competitor repos related to Scrapalot
# Usage: search_repos.sh <max_repos> [sort_by] [min_stars]
# sort_by: stars (default), updated, forks

MAX_REPOS=${1:-10}
SORT_BY=${2:-stars}
MIN_STARS=${3:-20}

QUERIES=(
  # ========================================
  # CATEGORY 1: Direct RAG platform competitors (products with UI)
  # ========================================
  "RAG platform open source self-hosted"
  "AI knowledge base chat self-hosted"
  "document QA platform open source"
  "open source AI chat documents upload"
  "private GPT documents self-hosted"
  "local AI assistant PDF knowledge base"

  # ========================================
  # CATEGORY 2: AI research & writing tools
  # ========================================
  "AI research assistant paper writing"
  "AI literature review tool"
  "academic research assistant open source"
  "AI paper writing assistant citations"
  "scientific writing assistant LLM"
  "AI citation manager references"

  # ========================================
  # CATEGORY 3: AI Scientist / Deep Research
  # ========================================
  "deep research AI agent autonomous"
  "AI scientist research automated"
  "automated literature review system"

  # ========================================
  # CATEGORY 4: Text editors & rich text writing tools
  # ========================================
  "rich text editor open source collaborative"
  "markdown editor open source WYSIWYG"
  "block editor open source Notion-like"
  "collaborative text editor real-time"
  "AI writing editor open source"
  "distraction-free writing tool open source"
  "long-form writing tool open source"
  "novel writing tool open source"
  "screenplay writing software open source"
  "technical writing tool documentation"
  "ProseMirror editor open source"
  "TipTap editor application"
  "Slate editor application"
  "WYSIWYG editor modern open source"

  # ========================================
  # CATEGORY 5: Science & academic tools
  # ========================================
  "electronic lab notebook open source"
  "laboratory information management LIMS"
  "experiment tracking open source science"
  "research data management platform"
  "scientific workflow management tool"
  "bibliography manager open source"
  "citation manager open source"
  "reference manager open source"
  "systematic review tool open source"
  "LaTeX editor collaborative open source"
  "academic writing tool open source"
  "scientific manuscript writing tool"

  # ========================================
  # CATEGORY 6: Chat & messaging platforms
  # ========================================
  "open source chat platform self-hosted"
  "team chat open source Slack alternative"
  "real-time messaging platform open source"
  "AI chat platform open source"
  "group chat application open source"
  "encrypted chat open source self-hosted"
  "chat application WebSocket open source"

  # ========================================
  # CATEGORY 7: Collaboration & workspace tools
  # ========================================
  "open source Notion alternative"
  "collaborative workspace open source"
  "team collaboration tool self-hosted"
  "real-time collaboration platform open source"
  "shared workspace knowledge base"
  "project management knowledge open source"
  "wiki collaboration open source self-hosted"
  "whiteboard collaboration open source"

  # ========================================
  # CATEGORY 8: Knowledge management + note-taking + AI
  # ========================================
  "AI note-taking knowledge graph"
  "second brain AI knowledge management"
  "AI knowledge graph personal"
  "knowledge base wiki self-hosted"
  "personal wiki knowledge management"
  "note taking app markdown graph"
  "zettelkasten software open source"
  "PKM personal knowledge management open source"

  # ========================================
  # CATEGORY 9: Document understanding & processing
  # ========================================
  "PDF AI chat document understanding"
  "document intelligence AI extraction"
  "book reader AI summary"
  "ebook reader AI assistant"
  "PDF reader AI annotations"
  "document management system self-hosted"

  # ========================================
  # CATEGORY 10: Enterprise AI search & QA
  # ========================================
  "enterprise search AI semantic open source"
  "workplace AI search knowledge"
  "AI search engine documents self-hosted"

  # ========================================
  # CATEGORY 11: Research discovery & literature
  # ========================================
  "paper discovery tool academic"
  "literature search engine open source"
  "connected papers alternative open source"
  "research paper recommendation system"

  # ========================================
  # CATEGORY 12: Specific product competitors (by name)
  # ========================================
  "Quivr AI second brain"
  "AnythingLLM documents chat"
  "PrivateGPT local documents"
  "Danswer enterprise AI search"
  "Perplexica AI search engine"
  "Kotaemon document QA"
  "Rocket.Chat open source"
  "Mattermost open source"
  "Element Matrix chat"
  "Zulip chat open source"
  "HedgeDoc collaborative markdown"
  "Etherpad collaborative editor"
  "CryptPad encrypted collaboration"
  "BookStack documentation wiki"
  "Wiki.js knowledge base"
  "Foam VS Code knowledge"
  "Trilium notes knowledge"
  "Joplin notes open source"
  "Standard Notes encrypted"
  "Laverna notes markdown"

  # ========================================
  # CATEGORY 13: Specific science products (by name)
  # ========================================
  "Zotero alternative open source"
  "Mendeley alternative open source"
  "Logseq knowledge graph"
  "JabRef bibliography"
  "calibre ebook management"
  "eLabFTW electronic lab notebook"
  "SciNote electronic lab notebook"
  "Overleaf alternative self-hosted"
  "Paperless-ngx document management"

  # ========================================
  # CATEGORY 14: Specific editor/writing products (by name)
  # ========================================
  "Novel editor open source AI"
  "Tiptap editor platform"
  "Yoopta editor blocks"
  "Plate editor open source"
  "BlockNote editor"
  "Milkdown editor markdown"
  "Docmost wiki collaborative"
  "Huly project management"
  "Plane project management"

  # ========================================
  # CATEGORY 15: Research & collaboration platforms
  # ========================================
  "research collaboration platform open source"
  "scientific project management tool"
  "research team collaboration tool"
  "research operating system platform"
  "all-in-one research tool open source"

  # ========================================
  # CATEGORY 16: Topic-based searches
  # ========================================
  "topic:rich-text-editor"
  "topic:collaborative-editing"
  "topic:text-editor"
  "topic:markdown-editor"
  "topic:chat-application"
  "topic:team-chat"
  "topic:electronic-lab-notebook"
  "topic:research-tool"
  "topic:bibliography"
  "topic:citation-manager"
  "topic:knowledge-management"
  "topic:note-taking"
  "topic:zettelkasten"
  "topic:document-management"
  "topic:collaboration"
  "topic:wiki"
  "topic:writing-tool"
)

SEEN=""

for QUERY in "${QUERIES[@]}"; do
  RESULTS=$(gh api "search/repositories?q=$(echo "$QUERY" | sed 's/ /+/g')+stars:>$MIN_STARS&sort=$SORT_BY&order=desc&per_page=$MAX_REPOS" \
    --jq '.items[] | {full_name, html_url, description, stargazers_count, pushed_at, language, topics, size}' 2>/dev/null)

  while IFS= read -r line; do
    NAME=$(echo "$line" | jq -r '.full_name' 2>/dev/null)
    if [ -n "$NAME" ] && [[ ! "$SEEN" == *"$NAME"* ]]; then
      SEEN="$SEEN $NAME"
      echo "$line"
    fi
  done <<< "$RESULTS"
done | head -n "$MAX_REPOS"
