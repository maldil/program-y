import logging

from programy.mappings.base import BaseCollection
from programy.rdf.entity import RDFEntity
from programy.utils.files.filefinder import FileFinder


class RDFLoader(FileFinder):
    def __init__(self, collection):
        FileFinder.__init__(self)
        self._collection = collection

    def load_file_contents(self, filename):
        if logging.getLogger().isEnabledFor(logging.DEBUG):
            logging.debug("Loading RDF File [%s]", filename)
        try:
            self._collection.load_from_filename(filename)
        except Exception as excep:
            if logging.getLogger().isEnabledFor(logging.ERROR):
                logging.error("Failed to load RDF File [%s] - %s", filename, excep)


class RDFCollection(BaseCollection):

    def __init__(self):
        BaseCollection.__init__(self)
        self._subjects = {}
        self._entities = []

    def split_line(self, line):
        splits = self.split_line_by_char(line)
        if len(splits) > 3:
            return [splits[0], splits[1], self.get_split_char().join(splits[2:])]
        return splits

    def get_split_char(self):
        return ":"

    def get_split_pattern(self):
        return ".*"

    def split_line_by_char(self, line):
        splits = line.split(self.get_split_char())
        return splits

    def process_splits(self, splits):
        self.add_entity(splits[0], splits[1], splits[2])
        return True

    def has_subject(self, rdf_subject):
        return bool(rdf_subject.upper() in self._subjects)

    def subjects(self):
        return self._subjects.keys()

    def has_predicate(self, rdf_subject, rdf_predicate):
        if self.has_subject(rdf_subject):
            return bool(rdf_predicate.upper() in self._subjects[rdf_subject.upper()])
        return False

    def predicates(self, rdf_subject):
        return list(self._subjects[rdf_subject.upper()].keys())

    def has_object(self, rdf_subject, rdf_predicate, rdf_object):
        if self.has_subject(rdf_subject):
            if self.has_predicate(rdf_subject, rdf_predicate):
                return bool(rdf_object in self._subjects[rdf_subject.upper()][rdf_predicate.upper()])
        return False

    def objects(self, rdf_subject, rdf_predicate):
        return list(self._subjects[rdf_subject.upper()][rdf_predicate.upper()].keys())

    def add_entity(self, rdf_subject, rdf_predicate, rdf_object):

        if rdf_subject is not None:
            rdf_subject = rdf_subject.upper()
        if rdf_predicate is not None:
            rdf_predicate = rdf_predicate.upper()

        if self.has_subject(rdf_subject) is False:
            logging.debug("Adding new RDF Subject (%s)"%rdf_subject)
            self._subjects[rdf_subject] = {}

        if self.has_predicate(rdf_subject, rdf_predicate) is False:
            logging.debug("Adding new RDF Predicate (%s, %s)"%(rdf_subject, rdf_predicate))
            self._subjects[rdf_subject][rdf_predicate] = {}

        if self.has_object(rdf_subject, rdf_predicate, rdf_object) is False:
            entity = RDFEntity(rdf_subject, rdf_predicate, rdf_object)
            logging.debug("Adding RDF Entity (%s, %s, %s)" % (rdf_subject, rdf_predicate, rdf_object))
            self._subjects[rdf_subject][rdf_predicate][rdf_object] = entity
            self._entities.append(entity)
        else:
            if logging.getLogger().isEnabledFor(logging.WARNING):
                logging.warning("Duplicate RDF Entity [%s][%s][%s]", rdf_subject, rdf_predicate, rdf_object)

    def delete_entity(self, rdf_subject, rdf_predicate=None, rdf_object=None):

        if rdf_subject is not None:
            rdf_subject = rdf_subject.upper()
        if rdf_predicate is not None:
            rdf_predicate = rdf_predicate.upper()

        if rdf_predicate is not None and rdf_object is not None and self.has_object(rdf_subject, rdf_predicate, rdf_object):
            logging.debug ("Removing RDF Entity (%s, %s, %s)"%(rdf_subject, rdf_predicate, rdf_object))
            self._entities.remove(self._subjects[rdf_subject][rdf_predicate][rdf_object])
            del self._subjects[rdf_subject][rdf_predicate][rdf_object]

        elif rdf_predicate is not None and self.has_predicate(rdf_subject, rdf_predicate):
            obj_keys = []
            for pred_object in self._subjects[rdf_subject][rdf_predicate]:
                self._entities.remove(self._subjects[rdf_subject][rdf_predicate][pred_object])
                obj_keys.append(pred_object)
            for key in obj_keys:
                logging.debug("Removing RDF Entity (%s, %s, %s)" % (rdf_subject, rdf_predicate, key))
                del self._subjects[rdf_subject][rdf_predicate][key]
            logging.debug("Removing RDF Predicate (%s, %s)" % (rdf_subject, rdf_predicate))
            del self._subjects[rdf_subject][rdf_predicate]

        elif self.has_subject(rdf_subject):
            pred_keys = []
            for predicate in self._subjects[rdf_subject]:
                obj_keys = []
                for subj_object in self._subjects[rdf_subject][predicate]:
                    self._entities.remove(self._subjects[rdf_subject][predicate][subj_object])
                    obj_keys.append(subj_object)
                for key in obj_keys:
                    logging.debug("Removing RDF Entity (%s, %s, %s)" % (rdf_subject, predicate, key))
                    del self._subjects[rdf_subject][predicate][key]
                pred_keys.append(predicate)
            for key in pred_keys:
                logging.debug("Removing RDF Predicate (%s, %s)" % (rdf_subject, key))
                del self._subjects[rdf_subject][key]
            logging.debug("Removing RDF Subject (%s)" % (rdf_subject))
            del self._subjects[rdf_subject]

    def match(self, rdf_subject=None, rdf_predicate=None, rdf_object=None):

        if rdf_subject is not None:
            rdf_subject = rdf_subject.upper()
        if rdf_predicate is not None:
            rdf_predicate = rdf_predicate.upper()

        logging.debug("RDF Matching (%s, %s, %s)"%(rdf_subject, rdf_predicate, rdf_object))

        entities = []
        if rdf_subject is None:
            for for_subject in self._subjects:
                if rdf_predicate is None:
                    for for_predicate in self._subjects[for_subject]:
                        if rdf_object is None:
                            for for_object in self._subjects[for_subject][for_predicate]:
                                logging.debug("RDF Matched (%s, %s, %s)" % (for_subject, for_predicate, for_object))
                                entities.append(self._subjects[for_subject][for_predicate][for_object])
                        elif self.has_object(for_subject, for_predicate, rdf_object):
                            logging.debug("RDF Matched (%s, %s, %s)" % (for_subject, for_predicate, rdf_object))
                            entities.append(self._subjects[for_subject][for_predicate][rdf_object])
                elif self.has_predicate(for_subject, rdf_predicate):
                    if rdf_object is None:
                        for for_object in self._subjects[for_subject][rdf_predicate]:
                            logging.debug("RDF Matched (%s, %s, %s)" % (for_subject, rdf_predicate, for_object))
                            entities.append(self._subjects[for_subject][rdf_predicate][for_object])
                    elif self.has_object(for_subject, rdf_predicate, rdf_object):
                        logging.debug("RDF Matched (%s, %s, %s)" % (for_subject, rdf_predicate, rdf_object))
                        entities.append(self._subjects[for_subject][rdf_predicate][rdf_object])
        else:
            if self.has_subject(rdf_subject):
                if rdf_predicate is None:
                    for for_predicate in self._subjects[rdf_subject]:
                        if rdf_object is None:
                            for for_object in self._subjects[rdf_subject][for_predicate]:
                                logging.debug("RDF Matched (%s, %s, %s)" % (rdf_subject, for_predicate, for_object))
                                entities.append(self._subjects[rdf_subject][for_predicate][for_object])
                        elif self.has_object(rdf_subject, for_predicate, rdf_object):
                            logging.debug("RDF Matched (%s, %s, %s)" % (rdf_subject, for_predicate, rdf_object))
                            entities.append(self._subjects[rdf_subject][for_predicate][rdf_object])
                elif self.has_predicate(rdf_subject, rdf_predicate):
                    if rdf_object is None:
                        for for_object in self._subjects[rdf_subject][rdf_predicate]:
                            logging.debug("RDF Matched (%s, %s, %s)" % (rdf_subject, rdf_predicate, for_object))
                            entities.append(self._subjects[rdf_subject][rdf_predicate][for_object])
                    elif self.has_object(rdf_subject, rdf_predicate, rdf_object):
                        logging.debug("RDF Matched (%s, %s, %s)" % (rdf_subject, rdf_predicate, rdf_object))
                        entities.append(self._subjects[rdf_subject][rdf_predicate][rdf_object])

        logging.debug("RDF Matched a total of %d entities"%len(entities))
        return entities

    def not_match(self, rdf_subject=None, rdf_predicate=None, rdf_object=None):

        logging.debug("RDF Not Matching (%s, %s, %s)"%(rdf_subject, rdf_predicate, rdf_object))

        entities = self._entities[:]
        matched = self.match(rdf_subject, rdf_predicate, rdf_object)

        to_remove = []
        for match in matched:
            for entity in entities:
                if entity.subject == match.subject:
                    to_remove.append(entity)

        for rem in to_remove:
            if rem in entities:
                entities.remove(rem)

        logging.debug("RDF Not Matched a total of %d entities"%len(entities))
        return entities

    def load(self, configuration):
        loader = RDFLoader(self)
        if configuration.files is not None:
            files = []
            for file in configuration.files:
                files += loader.load_dir_contents(file, configuration.directories, configuration.extension)
            return len(files)
        self._subjects = {}
        self._entities = []
        return 0
