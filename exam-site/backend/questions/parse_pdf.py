"""
Parse AI训练师初赛题库 PDF into structured JSON questions.
"""
import fitz, sys, re, json
sys.stdout.reconfigure(encoding='utf-8')

def parse_all_questions():
    doc = fitz.open(
        r'D:\work\idea\examjincompitition\doc\人工智能训练师初赛理论500题库 (1).pdf'
    )
    full_text = ''
    for i in range(doc.page_count):
        full_text += doc[i].get_text()

    # Split into 3 sections
    sections = {}
    for header, key in [
        ('一、单选题（共300 题）', 'single'),
        ('二、多选题（共70 题）', 'multiple'),
        ('三、判断题（共130 题）', 'truefalse'),
    ]:
        idx = full_text.find(header)
        if idx < 0:
            # Try alternate format
            idx = full_text.find(key)
        sections[key] = {'start': idx, 'text': ''}

    # Set boundaries
    sec_keys = ['single', 'multiple', 'truefalse']
    for j, k in enumerate(sec_keys):
        start = sections[k]['start']
        end = sections[sec_keys[j+1]]['start'] if j+1 < len(sec_keys) else len(full_text)
        sections[k]['text'] = full_text[start:end]

    questions = []

    # --- Parse single choice ---
    text = sections['single']['text']
    # Remove the header line
    header_end = text.find('\n1.')
    if header_end < 0:
        header_end = text.find('1.')
    text = text[header_end:]

    # Pattern: number. question text... options... 【答案】X
    # Handle multi-line questions
    # Split by question number pattern
    parts = re.split(r'\n(?=\d+\.)', text)
    for part in parts:
        part = part.strip()
        if not part:
            continue
        # Extract answer first (from 【答案】)
        ans_match = re.search(r'【答案】\s*([A-E]+)', part)
        if not ans_match:
            continue
        answer = ans_match.group(1)

        # Extract options
        opts = {}
        opt_pattern = re.findall(r'([A-E])\.\s*(.+?)(?=\n[A-E]\.|\n【答案】|$)', part, re.DOTALL)
        for opt_letter, opt_text in opt_pattern:
            opts[opt_letter] = opt_text.strip()

        if not opts:
            continue

        # Extract question text (everything before options)
        # Remove options and answer from part
        q_text_part = re.sub(r'[A-E]\.\s*.+?(?=\n[A-E]\.|\n【答案】)', '', part, flags=re.DOTALL)
        q_text_part = re.sub(r'【答案】.+', '', q_text_part).strip()
        # Remove the leading number
        q_text_part = re.sub(r'^\d+\.\s*', '', q_text_part).strip()

        if not q_text_part:
            continue

        # Get question number
        num_match = re.match(r'(\d+)', part)
        question_num = int(num_match.group(1)) if num_match else len(questions) + 1

        questions.append({
            'id': question_num,
            'type': 'single',
            'question': q_text_part,
            'options': opts,
            'answer': answer,
        })

    print(f'Single choice: {len([q for q in questions if q["type"]=="single"])}')

    # --- Parse multiple choice ---
    text = sections['multiple']['text']
    header_end = text.find('\n1.')
    if header_end < 0:
        header_end = text.find('1.')
    text = text[header_end:]

    parts = re.split(r'\n(?=\d+\.)', text)
    for part in parts:
        part = part.strip()
        if not part:
            continue
        ans_match = re.search(r'【答案】\s*([A-E]+)', part)
        if not ans_match:
            continue
        answer = ans_match.group(1)

        opts = {}
        opt_pattern = re.findall(r'([A-E])\.\s*(.+?)(?=\n[A-E]\.|\n【答案】|$)', part, re.DOTALL)
        for opt_letter, opt_text in opt_pattern:
            opts[opt_letter] = opt_text.strip()

        if not opts:
            continue

        q_text_part = re.sub(r'[A-E]\.\s*.+?(?=\n[A-E]\.|\n【答案】)', '', part, flags=re.DOTALL)
        q_text_part = re.sub(r'【答案】.+', '', q_text_part).strip()
        q_text_part = re.sub(r'^\d+\.\s*', '', q_text_part).strip()

        if not q_text_part:
            continue

        num_match = re.match(r'(\d+)', part)
        question_num = int(num_match.group(1)) if num_match else len(questions) + 1

        questions.append({
            'id': question_num,
            'type': 'multiple',
            'question': q_text_part,
            'options': opts,
            'answer': answer,
        })

    print(f'Multiple choice: {len([q for q in questions if q["type"]=="multiple"])}')

    # --- Parse true/false ---
    text = sections['truefalse']['text']
    header_end = text.find('\n1.')
    if header_end < 0:
        header_end = text.find('1.')
    text = text[header_end:]

    parts = re.split(r'\n(?=\d+\.)', text)
    for part in parts:
        part = part.strip()
        if not part:
            continue
        ans_match = re.search(r'【答案】\s*([AB])', part)
        if not ans_match:
            continue
        answer = ans_match.group(1)

        opts = {'A': '正确', 'B': '错误'}

        q_text_part = re.sub(r'A\.\s*正确', '', part)
        q_text_part = re.sub(r'B\.\s*错误', '', q_text_part)
        q_text_part = re.sub(r'【答案】.+', '', q_text_part).strip()
        q_text_part = re.sub(r'^\d+\.\s*', '', q_text_part).strip()
        q_text_part = re.sub(r'\(\s*\)', '', q_text_part).strip()
        q_text_part = re.sub(r'。\s*$', '', q_text_part).strip()

        if not q_text_part:
            continue

        num_match = re.match(r'(\d+)', part)
        question_num = int(num_match.group(1)) if num_match else len(questions) + 1

        questions.append({
            'id': question_num,
            'type': 'truefalse',
            'question': q_text_part,
            'options': opts,
            'answer': answer,
        })

    print(f'True/false: {len([q for q in questions if q["type"]=="truefalse"])}')
    print(f'Total: {len(questions)}')

    return questions


if __name__ == '__main__':
    questions = parse_all_questions()
    output_path = (
        r'D:\work\idea\examjincompitition\exam-site\backend\questions\questions.json'
    )
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)
    print(f'Saved to {output_path}')

    # Check quality
    for qtype in ['single', 'multiple', 'truefalse']:
        subset = [q for q in questions if q['type'] == qtype]
        if subset:
            print(f'\n{qtype} sample:')
            print(f'  Q{subset[0]["id"]}: {subset[0]["question"][:50]}')
            print(f'  Options: {subset[0]["options"]}')
            print(f'  Answer: {subset[0]["answer"]}')
