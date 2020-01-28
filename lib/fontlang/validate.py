"""
A CLI script to check rosetta.yaml is well-formed
"""
import logging
import yaml
import re
from Languages import Languages


VALID_TODOS = ["done", "weak", "todo", "strong"]


def check_yaml():
    logging.info("Checking yaml structure...")

    try:
        Languages()
    except yaml.scanner.ScannerError as e:
        logging.error("Malformed yaml:")
        print(e)
    except yaml.parser.ParserError as e:
        logging.error("Malformed yaml:")
        print(e)


def check_types():
    Langs = Languages()

    for iso, lang in Langs.items():
        if "includes" in lang:
            if not check_is_valid_list(lang["includes"]):
                logging.error("'%s' has invalid list 'includes'" % iso)

        if "source" in lang:
            if not check_is_valid_list(lang["source"]):
                logging.error("'%s' has invalid list 'source'" % iso)

        if "orthographies" in lang:
            if not check_is_valid_list(lang["orthographies"]):
                logging.error("'%s' has invalid list 'orthographies'" % iso)

            for o in lang["orthographies"]:
                if "base" in o:
                    if not check_is_valid_glyph_string(o["base"]):
                        logging.error("'%s' has invalid 'base' glyph list"
                                      % iso)

                if "combinations" in o:
                    if not check_is_valid_combation_string(o["combinations"]):
                        logging.error("'%s' has invalid 'combination' string"
                                      % iso)

        if "name" not in lang and "preferred_name" not in lang:
            logging.error("'%s' has neither 'name' nor 'preferred_name'" % iso)

        if "name" in lang and "preferred_name" in lang and \
                lang["name"] == lang["preferred_name"]:
            logging.error("'%s' has 'name' and 'preferred_name', but they are "
                          "identical" % iso)

        if "todo_status" in lang and lang["todo_status"] not in VALID_TODOS:
            logging.error("'%s' has an invalid 'todo_status'" % iso)


def check_is_valid_list(item):
    """
    item should be a list and should not be empty
    """
    if type(item) is not list or len(item) < 1:
        return False

    return True


def check_is_valid_glyph_string(glyphs):
    """
    a string of glyphs like "a b c d e f" should be single-space separated
    single unicode characters
    """
    if type(glyphs) is not str or len(glyphs) < 1:
        return False

    if re.findall(r" {2,}", glyphs):
        logging.error("More than single space in '%s'" % glyphs)
        return False

    return True


def check_is_valid_combation_string(combos):
    """
    combinations should be quote-wrapped and each glyph wrapped in {}

    @example: '{а̄}{е̄}{ә̄}{о̄}{ы̄}'
    """
    if type(combos) is not str or len(combos) == 0:
        return False

    if re.findall(r"\s", combos):
        logging.error("'combination' may not contain white space")
        return False

    # Remove beginning {, ending }, or pairs of }{ — if any { or } remain,
    # there was a "syntax" error in the data
    removed = re.sub(r"(^\{)|(\}\{)|(\}$)", "", combos)
    if re.findall(r"\{|\}", removed):
        logging.error("'combination' has invalid pattern of curly braces")
        return False

    return True


def check_names():
    Langs = Languages()

    for iso, lang in Langs.items():
        if "orthographies" in lang:
            for o in lang["orthographies"]:
                if "base" not in o:
                    logging.error("'%s' has an orthography which is missing a "
                                  "'base' attribute" % iso)
                    continue
                if "autonym" not in o:
                    logging.error("'%s' has an orthography which is missing an"
                                  " 'autonym'" % iso)
                    continue
                autonym_ok, chars, missing = check_autonym_spelling(o)
                if not autonym_ok:
                    logging.error("'%s' has invalid autonym '%s' which cannot "
                                  "be spelled with that orthography's charset "
                                  "'%s' - missing '%s'"
                                  % (iso, o["autonym"], "".join(chars),
                                     "".join(missing)))


def check_autonym_spelling(ort):
    chars = ort["base"]
    if "auxiliary" in ort:
        chars = chars + ort["auxiliary"]

    chars = set(ort["base"])

    # Use the autonym in lowercase and without any "non-word" marks (hyphens,
    # apostrophes, etc.)
    ignore_punctuation = re.compile("|".join(["\W", "ʼ", "ʻ"])) # noqa
    autonym = ort["autonym"].lower()
    autonym = ignore_punctuation.sub("", autonym)

    autonym = set(autonym)
    missing = list(autonym.difference(chars))

    return autonym.issubset(chars), list(chars), missing


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    check_yaml()
    check_types()
    check_names()