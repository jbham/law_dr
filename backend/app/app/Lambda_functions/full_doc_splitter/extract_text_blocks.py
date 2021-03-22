import re
from typing import List, Any


def extract_text_blocks(got_text):
    original_t = ""
    original_t_for = str()
    for nt in got_text["blocks"]:
        if nt["type"] == 0:

            # below list comprehension is equivalent to this:
            #         for each_line in nt["lines"]:
            #             for each_span in each_line["spans"]:
            #                 original_t_for += each_span["text"]

            original_t_list: List[Any] = [each_span["text"] for each_line in nt["lines"] for each_span in
                                          each_line["spans"]]

            intermediate_text = ''.join(original_t_list)
            # if original_t ends with any number then add some string with newline character
            # so that CTAKES doesn't mess up in identifying measurements or date annotations
            m = re.search(r'\d+$', intermediate_text)
            if m is not None:
                intermediate_text += " SamKamJas.\n"
                # elif original_t.endswith("."):
                #     original_t += "\n"
            else:
                intermediate_text += "\n"

            # remove bullet list character
            if u'\u2022' in intermediate_text:
                intermediate_text = intermediate_text.replace(u'\u2022', ".")

            original_t += intermediate_text

    return original_t
