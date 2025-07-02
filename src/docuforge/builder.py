from typing import List, Union, Dict, Any, Optional
from .models import DocumentData, Section, ImageData

class DocumentBuilder:
    """
    Builder for stepwise, agent-friendly construction of DocumentData.
    """
    def __init__(self):
        self._title: Optional[str] = None
        self._sections: List[Section] = []
        self._images: List[ImageData] = []
        self._meta: Dict[str, Any] = {}

    def set_title(self, title: str):
        self._title = title
        return self

    def add_section(self, section: Union[Section, Dict[str, Any]]):
        if isinstance(section, dict):
            section = Section(**{k: v for k, v in section.items() if k in Section.__dataclass_fields__})
        if not isinstance(section, Section):
            raise TypeError("section must be Section or dict")
        self._sections.append(section)
        return self

    def add_sections(self, sections: List[Union[Section, Dict[str, Any]]]):
        for s in sections:
            self.add_section(s)
        return self

    def add_image(self, image: Union[ImageData, Dict[str, Any]]):
        if isinstance(image, dict):
            image = ImageData(**{k: v for k, v in image.items() if k in ImageData.__dataclass_fields__})
        if not isinstance(image, ImageData):
            raise TypeError("image must be ImageData or dict")
        self._images.append(image)
        return self

    def add_images(self, images: List[Union[ImageData, Dict[str, Any]]]):
        for img in images:
            self.add_image(img)
        return self

    def set_meta(self, meta: Dict[str, Any]):
        self._meta = dict(meta)
        return self

    def clear(self):
        self._title = None
        self._sections = []
        self._images = []
        self._meta = {}
        return self

    def build(self) -> DocumentData:
        if not self._title:
            raise ValueError("Document title is required")
        return DocumentData(
            title=self._title,
            sections=list(self._sections),
            images=list(self._images),
            meta=dict(self._meta),
        )

    @classmethod
    def from_document(cls, doc: DocumentData) -> 'DocumentBuilder':
        builder = cls()
        builder.set_title(doc.title)
        builder.add_sections(doc.sections)
        builder.add_images(doc.images)
        builder.set_meta(doc.meta)
        return builder
