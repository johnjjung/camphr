from typing import Optional, List, Dict, Any, Callable
from collections import namedtuple

from bedoner.consts import KEY_FSTRING
from pyknp import Juman, Morpheme
from bedoner.lang.stop_words import STOP_WORDS
from spacy.attrs import LANG
from spacy.language import Language
from spacy.tokens import Doc, Token
from spacy.compat import copy_reg
from bedoner.utils import SerializationMixin


ShortUnitWord = namedtuple("ShortUnitWord", ["surface", "lemma", "pos", "fstring"])


class Tokenizer(SerializationMixin):
    """Juman tokenizer"""

    serialization_fields = ["preprocessor", "juman_kwargs"]

    def __init__(
        self,
        cls,
        nlp: Optional[Language] = None,
        juman_kwargs: Optional[Dict[str, str]] = None,
        preprocessor: Optional[Callable[[str], str]] = None,
    ):
        """Init

        Args:
            juman_kwargs: passed to pyknp.Juman's constructor
            preprocessor: apply before tokenizing.
        """
        self.vocab = nlp.vocab if nlp is not None else cls.create_vocab(nlp)
        self.tokenizer = Juman(**juman_kwargs) if juman_kwargs else Juman()
        self.key_fstring = KEY_FSTRING
        Token.set_extension(self.key_fstring, default=False, force=True)
        self.preprocessor = preprocessor

    def __call__(self, text: str) -> Doc:
        """Make doc from text"""
        if self.preprocessor:
            text = self.preprocessor(text)
        dtokens = self.detailed_tokens(text)
        words = [x.surface for x in dtokens]
        spaces = [False] * len(words)
        doc = Doc(self.vocab, words=words, spaces=spaces)
        for token, dtoken in zip(doc, dtokens):
            token.lemma_ = dtoken.lemma
            token.tag_ = dtoken.pos
            token._.set(self.key_fstring, dtoken.fstring)
        return doc

    def detailed_tokens(self, text) -> List[Morpheme]:
        """Format juman output for tokenizing"""
        words = []
        ml = self.tokenizer.analysis(text).mrph_list()
        for m in ml:
            # m: Morpheme = m
            surface = m.midasi
            pos = m.hinsi + "/" + m.bunrui
            lemma = m.genkei or surface
            words.append(ShortUnitWord(surface, lemma, pos, m.fstring))
        return words


class Defaults(Language.Defaults):
    lex_attr_getters = dict(Language.Defaults.lex_attr_getters)
    lex_attr_getters[LANG] = lambda _text: "juman"
    stop_words = STOP_WORDS
    writing_system = {"direction": "ltr", "has_case": False, "has_letters": False}

    @classmethod
    def create_tokenizer(
        cls,
        nlp=None,
        juman_kwargs: Optional[Dict[str, Any]] = None,
        preprocessor: Optional[Callable[[str], str]] = None,
    ):
        return Tokenizer(cls, nlp, juman_kwargs=juman_kwargs, preprocessor=preprocessor)


class Japanese(Language):
    lang = "juman"
    Defaults = Defaults

    def make_doc(self, text: str) -> Doc:
        return self.tokenizer(text)


def pickle_japanese(instance):
    return Japanese, tuple()


copy_reg.pickle(Japanese, pickle_japanese)


__all__ = ["Japanese"]
