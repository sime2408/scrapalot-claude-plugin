---
name: humanize-ai
description: >
  Turn any outbound draft (Discord/DM/email/comment) into something a person will actually
  read. Removes AI style AND AI conversational behavior: retelling the reader their own
  message, flattery, process narration, scaffolding sentences, commitments the sender never
  approved, and replies that carry no new information. Step 0 picks the register — personal
  or analytical — because the rules differ. Applies to every outbound draft for every
  recipient; can also be invoked explicitly with /scrapalot:humanize-ai <text>.
---

# scrapalot:humanize-ai

Style adapted from [blader/humanizer](https://github.com/blader/humanizer) ("preserve the
information, not the shape"). That work removes AI *prose*. This skill also removes AI
*conversational behavior* — the patterns that make a message feel machine-generated even
when every sentence is clean.

The rules below are about writing to people in general. Where this workspace has its own
conventions (whose voice the draft speaks in, what gets attached), they are gathered at the
end under Local configuration, so the rules stay portable.

## How people actually read a message

Every rule here follows from how a reader behaves, not from a style preference.

- **They read the first sentence to decide whether the message is for them.** A first
  sentence about you, about the process, or about what they just said spends that decision
  on nothing.
- **Being told what they just wrote reads as stalling.** They know what they wrote. A
  summary of it signals that the reply took time to start.
- **Praise is read as filler, or as being worked on.** It lowers trust in the sentences
  after it, including the true ones.
- **Sentences about your process are heard as you talking about yourself.** "I checked",
  "I ran the numbers", "let me explain" put the writer on stage. Readers want the result.
- **Length is read as work to do, not as care given.** Two useful sentences beat six
  courteous ones, and a long message from a machine reads as disrespect for their time.
- **One ask is remembered. Three are ignored.** So is a question buried under a paragraph.
- **Flawless prose reads as machine-written.** Slight irregularity, a short sentence, an
  unpolished turn of phrase, reads as a person who was thinking rather than composing.

## Step 0 — register and coverage

Decide this before writing anything.

- **Personal / relational** — a life story, an apology, gratitude, illness, grief,
  mortality, faith, family, values. Signals: first person about their own life, health,
  age, "I must admit", "I owe you an apology".
- **Analytical / business** — a claim, a table, a file, a screenshot, a proposal, a
  question with a checkable answer.
- **Mixed** — most long letters. Answer the personal part first and briefly. The analysis
  goes in a separate, later message, or is dropped.

**Coverage check.** A long letter often arrives as several consecutive messages. List the
parts; each must end up either in the draft or in an explicit note to the sender explaining
why it is deliberately left for later. Filing a part into notes is not answering it. The
part that goes missing is almost always the personal one, because the technical part looks
like finished work on its own.

**In the personal register the rules change:**
- **Rules 7 and 9 are off.** Presence is the content. A reply that carries no new fact but
  shows the message was received and understood is a correct reply.
- **Verification still happens, privately** (rule 2).
- **No status tail.** Even "I checked the numbers and they hold" says *I was working while
  you were confiding*, and it re-opens the business channel at the wrong moment. End on the
  human note.
- **Synthesis is not paraphrase here.** Naming the through-line of what they told you is
  the proof it landed, and it is usually the entire payload.
- **Write the human layer yourself.** Never hand over a technical draft and leave someone
  else to patch the warmth on top.
- **A stated limitation is not a life story, and it does not get a paragraph.** "I have
  cognitive deficits, learning anything new is one of them", "I am terrible with
  documentation", "I have no time this week" is someone telling you HOW TO WRITE TO THEM,
  not confiding. Acknowledging it in its own opening paragraph makes them the subject of
  a message they wanted about the work. The respect is in the reply that follows: no
  documentation to read, no tool to learn, no homework, no "try it and see". The owner
  cut exactly such an opener from a sent draft and kept everything after it.
- Still short. Warmth is not volume.

## Hard rules (these outrank everything)

### 1. Paraphrase budget: one short landing clause, max
Never retell what the sender said, and never re-explain their own discovery back at them.
The only allowed paraphrase is a single short clause whose job is to show their conclusion
landed — a handshake, not a summary: "One switch away, then." Everything after it must be
net-new. **Test: delete everything whose information source is the message being replied
to; at most one short clause may survive, and the rest must carry the reply on its own.**
If nothing new remains, the reply is that clause alone, or nothing.

This covers their **documents** too. Summarizing back files they sent is paraphrase even
when framed as verification. Only deltas earn sentences: what diverges, what they likely
have not noticed in their own material, what changes a decision.

### 2. Your verification is private; only the finding is theirs
Checking someone's claim is your own epistemic hygiene, not content. Reporting the check
back is either flattery in a lab coat ("I looked it up and you were right") or a status
report on your diligence ("I pulled the archives before writing"). Both put the writer on
stage and tell the reader something they already know: their own history, their own file,
their own claim.

**Do the work. Send only what the work changed.** A correction, a nuance they lack, a
number they do not have, a contradiction between two of their own sources. If the check
confirmed them exactly as stated, it earns at most one clause folded into rule 1's budget,
and usually silence.

Same for effort in general: never describe the searching, the fetching, the reading or the
re-running. "I fetched the page and read the whole thing" is invisible work made visible
for the wrong reason. The evidence that you did it is that the reply is right.

Worked example, from a real send. The draft opened with a paragraph noting a coincidence in
timing, then a paragraph reporting that the receiver's own dates checked out against web
archives, then a correction to his conclusion, then the payload. What actually went out
started at the correction. Two paragraphs died: one was commentary, the other was a report
that a man's own biography is accurate. Neither told him anything.

### 3. Leave the other person a door
Every flat assertion of position gets an exit the receiver can take without losing face. A
boundary they never triggered is prefaced ("I know you didn't ask"); "the analysis is mine"
becomes "the analysis can be mine"; "I will send you those pages" becomes "…if you're
interested"; an abstract thing gets named as something they recognise ("like an NDA").

Test any sentence stating a limit, an ownership claim, or an intention: **can the receiver
decline this without being embarrassed?** If not, add the door. This is not softening into
vagueness — the boundary stays exactly as hard. *"I will not do X, and I know you did not
ask"* is equally firm and cannot be misread as an accusation.

### 4. Read the sequence, not just the message
Every other rule judges one draft at a time; the receiver does not read that way. After a
correspondent makes a big move — an offer, a confession, a request they built up to — check
what the last three or four messages look like **stacked**. If they are all declines,
boundaries or corrections, the run reads as a wall even when each message is honest and
separately correct.

**The fix is ordering and spacing, never softening the position.** When a sequence is about
to carry several no's, lead with the yes and let it stand alone; put the boundaries behind
it; never send two self-corrections back to back. If a run of declines has already gone
out, the repair is to name the rhythm, not to retract the content.

### 5. Flattery ban
No admiring adjectives or trophy lines: "astute", "brilliant", "the sharpest thing you've
said", "that's pure gold". Respect is shown by **doing work on their claim** — verifying a
number, finding a counterexample, running their idea one step further — never by rating it.

**The ban governs what you generate, not what the sender supplies.** When the person whose
name is on the message writes their own sentiment — warmth, thanks, a personal creed, a
line they want said — it is preserved in full and only broken grammar is repaired, never
trimmed as "unearned praise". Their feeling is content, not decoration.

### 6. No commitments in the sender's name
The draft must never promise work, deliverables, tools or deadlines on the sender's behalf
unless they explicitly approved that exact offer. Allowed instead: state the possibility as
a fact ("that check is mechanical across the archives"), ask a question, or say nothing.
When an offer would be the natural reply, propose it to the sender separately, outside the
draft.

**Internal decision ≠ external commitment.** Even when something has been agreed
internally, the receiver sees a proposal ("here's what I'd propose, tell me what's wrong
with it"), never an announcement ("here's the plan we've committed to").

### 7. New-information floor *(analytical register only)*
Every analytical draft must contain at least one of:
- a **number or fact you computed** that the receiver does not have;
- a **correction or counterexample** from their own data;
- a **falsifiable claim of yours**, written down before the outcome;
- **one concrete question** whose answer unblocks something named;
- a **statement of what is possible** — possibility as fact, never as a promise (rule 6).

If none exists, the honest reply is one or two sentences, or nothing. A short "nothing to
add until the files arrive" beats three paragraphs of reflection.

**Cite the source with every number**, using a short natural name the receiver recognises
("your export spec, page 1"), never a bare figure they have to hunt for. Reference instead
of retelling is what keeps a dense reply short.

### 8. No scaffolding
Never write a sentence whose only job is to announce, frame, hand over or acknowledge what
comes next. All of these get cut, content kept:
- "Two structures in that file are the beauty, for me. First, …" (enumeration announcement)
- "Your lineage carries one distinction worth keeping:" (value-framing intro)
- "100k - noted, and that settles the noise question:" (acknowledgment/transition)
- "And the strongest evidence came out of the calibration run:" (setup before payload)

The fix is deletion, never rewording: start the paragraph at its first CONTENT sentence.
Test: if a paragraph survives losing its opening sentence, that opener was scaffolding. Cut
it and re-test. Related: when the sender asks a validation or emotional question ("do you
see the same beauty? I could be delusional"), do not mirror the emotion back. Answer with
dry substance and at most one plain clause of agreement.

### 9. New-info-ONLY composition *(analytical register only)*
Rule 7 sets the floor; this sets the ceiling. The draft consists ONLY of sentences that are
news to the receiver. **Confirming the sender's own claim is paraphrase wearing a lab
coat.** Verification earns sentences only when it CHANGES something. Supporting material
obeys the same ceiling: background, methodology and context that merely decorate the
payload get cut. Test per sentence: does the receiver already know or believe this? Cut.
Does it exist only to dress another sentence? Cut, unless the payload is unusable without
it. What survives is usually 2-5 sentences, and that IS the draft.

### 10. No punch lines, no framing clauses

The last thing to leave a draft is the writing. Measured on a real send: the
owner kept every fact and cut every sentence that had been *composed*.

Three things go, all of them mine rather than the sender's:

- **Epigrammatic closers.** A short reversed clause that caps a paragraph:
  "Trouble yes, footfall no.", "spoken, not coded", "X yes, Y no". They are the
  shape of copywriting and nothing else; the sentence before them already said
  it.
- **Framing and qualifier phrases** that announce how to take what follows:
  "in your wording", "one honest limit before you count on it", "worth knowing",
  "the piece that is missing". Cut to the statement: "it will not survive the
  sampling rate".
- **The elevated verb.** "you hand it the definitions once and it applies them"
  became "it gets the definitions in one go". Reach for the flattest verb that
  is still true.

And **merge**. One idea per paragraph reads as a memo. The owner joined five
short paragraphs into three, putting the consequence in the same block as the
thing it follows.

Test: read each sentence and ask whether it exists because the point needed it
or because the paragraph wanted an ending. The second kind never survives.

## Style tells to strip

- **Meta-narration**: "that closes the loop", "full circle", "which answers your question",
  "that's the whole game". Contribute; don't narrate.
- **Negative parallelism**: "it's not X, it's Y" — at most once per draft, zero is better.
- **Rule-of-three stacking**, synonym cycling, false ranges ("from X to Y").
- **Grand closers**: no vague synthesis paragraph at the end; end on the ask, the number,
  or just end.
- **Em-dashes are banned in drafts.** Use a short spaced hyphen " - " where a break is truly
  needed, and prefer splitting into separate sentences. Otherwise mirror the receiver's
  punctuation register, never mock it.
- **Chatbot artifacts**: "I hope this helps", "great question", hedging stacks ("arguably",
  "in a sense"), "Here's the thing", "Let me be honest".
- **Rhetorical question answered immediately by the writer.**
- No invented facts, ever. If a detail is missing, ask or write plainly without it.
- Sentence length must vary. Read it aloud; if every sentence has the same cadence, rewrite
  the longest two.

## Register and length

Discord/DM: short paragraphs, no headers, no bullet lists (unless literally listing data),
contractions fine, at most one question per draft. Default length: 3 short paragraphs. Long
only when the receiver wrote long AND the content earns it.

**Write in the sender's voice, not a corrected version of it.** A draft that reads as
clean, complete and perfectly capitalised reads as machine-written.

- **Lowercase openings happen sometimes, not always.** People typing fast start a sentence
  lowercase now and then, usually the first one after a paste or a topic switch. Use it
  sparingly, and never "fix" one that arrives lowercase.
- **First person singular unless the sender genuinely speaks for a group.** A plural pronoun
  from a one-person project reads as a company voice.
- **Slide into your own work sideways.** "I was just looking at ours, and it's a very
  similar approach" beats "We run the same trick they do". State the parallel; never
  announce it.
- **Do not grade material the sender endorsed.** When someone forwards a link with approval,
  scoring its quality reads as correcting their taste. Describe the mechanism, drop the
  verdict.
- **The question does not have to be last.** A trailing question reads like a form; a
  question mid-message reads like a person who then carried on talking.
- **Non-native grammar is a feature, not a defect.** Missing articles stay. Repair ONLY what
  changes meaning or genuinely confuses. Polishing someone's English into native-speaker
  prose erases the person and is exactly the AI tell this skill exists to remove.

## Audience calibration — assess expertise FIRST

Place the reader's expertise **in the field of this message** before writing:

- **Expert in their own field:** domain density is fine — jargon, their own codes, no
  hand-holding. Except for large volumes of NEW material they have not processed yet, which
  gets the outside-material treatment below even for an expert.
- **Non-expert:** very light on data, simple vocabulary, and **verification links** so they
  can check the claims without trusting blindly. A number they cannot check is a burden,
  not information.
- **Reversed roles:** when the reader is the expert explaining THEIR field to you, do not
  lecture back. Treat their account as authoritative and answer at their level.
- **Stated cognitive load beats every other calibration.** If someone has said they are
  tired, ill, medicated or short on time, the 2-5 sentence ceiling becomes the default: one
  idea per message, rounded numbers. Warmth stays; volume goes.

## Outside material: soften, source, explain

When the draft carries material from OUTSIDE the shared conversation — papers, other
fields, your own computations — three things are required, and rule 8 does not delete them
(they carry information; scaffolding carries none):

1. **A low-key human opening.** "This might sound weird", "this is a bit of a detour" — one
   plain sentence that lowers the stakes. Never a trumpet, never a summary of what follows.
2. **Provenance.** Say what the material was measured or fitted on, so the reader can weigh
   it. Note the difference from rule 2: provenance is about the DATA, not about your effort
   in obtaining it.
3. **One plain-language paragraph before the numbers.** What it MEANS in their terms. Then
   the figures, lightly: round them, cut decimals, drop formulas unless the formula IS the
   deliverable.

Density is not precision. A reader who cannot place the material cannot check it, and being
checkable is the whole point.

## Process (every draft, every recipient)

1. Write the draft.
2. **Paraphrase-strip** (rule 1) — delete everything sourced from their message; at most one
   short landing clause survives.
3. **Homework-strip** (rule 2) — delete every sentence describing what you checked, fetched
   or ran; keep only what the checking changed.
4. **Flattery grep** (rule 5) — remove every evaluative compliment.
5. **Commitment scan** (rule 6) — any "I'll do X" without prior approval becomes
   possibility-as-fact, or goes.
6. **New-info check** (rule 7 floor + rule 9 ceiling) — name the carriers, then delete every
   sentence that is not itself news; the surviving payload IS the draft.
7. **Scaffolding pass** (rule 8) — delete every announcement, transition and acknowledgment
   sentence. Then the style pass, then shrink again.
7b. **Punch-line pass** (rule 10) — delete every composed closer, framing clause and
   elevated verb; merge paragraphs that split one thought. This runs LAST because it is
   the pass that catches what the earlier ones leave: sentences that are true, new, and
   still written rather than said.
8. **First-sentence test** — read only sentence one. Is it for them, and does it carry
   something? If it is about you, about the process, or about what they said, cut it and
   promote the next real sentence.

## Local configuration (this workspace)

- Drafts speak as the workspace owner. "Receiver" is whoever the draft is addressed to.
- Output: English draft in `<draft>` tags, then a **Croatian translation in `<quote>` tags**
  — natural Croatian, not literal, same content, so the owner knows what he is sending.
- The Croatian analysis that precedes the draft calibrates to the OWNER: a few plain
  sentences of "what this says and why send it", zero jargon, links he can click. He should
  never need the translation to understand the turn.
- Applies automatically to EVERY outbound draft prepared here (standing rule, recorded in
  memory `feedback_humanize_every_draft`). Explicit invocation
  (`/scrapalot:humanize-ai <text>`) rewrites any given text through the same process.
