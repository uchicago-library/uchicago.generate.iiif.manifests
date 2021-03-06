from argparse import ArgumentParser
from os import _exit, scandir, listdir, getcwd, makedirs, mkdir
from os.path import exists, join, basename, dirname
import json
from PIL import Image
import re
import string
from uuid import uuid4
from xml.etree import ElementTree
from urllib.parse import quote

def _find_all_apf_chos(path):
    for a_thing in scandir(path):
        if a_thing.is_dir():
            yield from _find_all_apf_chos(a_thing.path)
        else:
            matchable = re.compile(r"apf[/]\d{1}[/]apf\d{1}-\d{5}.tif").search(a_thing.path)
            if matchable:
                yield a_thing.path


def find_all_photo_chos(path):
    for p in scandir(path):
        if p.is_dir():
            yield from find_all_ph

def _main():
    arguments = ArgumentParser()
    arguments.add_argument("path_to_issues", type=str, action='store')
    arguments.add_argument("path_to_metadata", type=str, action='store')
    parsed_args = arguments.parse_args()
    try:
        metadata = [x.path for x in scandir(parsed_args.path_to_metadata)]
        chos = _find_all_apf_chos(parsed_args.path_to_issues)
        for n in chos:
            basef = basename(n).split('.tif')[0]
            mdata_filestring = 'oai_dc' + basef
            creators = None
            subjects = None
            identifiers = None
            titles = None
            dates = None
            formats = None
            main_identifier = n.split("/data/voldemort/digital_collections/data/ldr_oc_admin/files/IIIF_Files/")[1]
            flat_identifier = main_identifier.split(".tif")[0] + ".json"
            print(flat_identifier)
            manifest_id = "https://iiif-manifest.lib.uchicago.edu/" + flat_identifier
            outp = {}
            outp["@context"] = "http://iiif.io/api/presentation/2/context.json"
            outp["@id"] = manifest_id
            outp["@type"] = "sc:Manifest"
            outp["metadata"] = []
            outp["license"] = "http://photoarchive.lib.uchicago.edu/rights.html"
            outp["logo"] = "https://www.lib.uchicago.edu/static/base/images/color-logo.png"
            outp["attribution"] = "University of Chicago Library"
            for m in metadata:
                if basef in m:
                    root = ElementTree.parse(m).getroot()
                    titles = [x.text for x in root.findall("{http://purl.org/dc/elements/1.1/}title")]
                    creators = [x.text for x in root.findall("{http://purl.org/dc/elements/1.1/}creator")]
                    dates = [x.text for x in root.findall("{http://purl.org/dc/elements/1.1/}date")]
                    identifiers = [x.text for x in root.findall("{http://purl.org/dc/elements/1.1/}identifier")]
                    subjects = [x.text for x in root.findall("{http://purl.org/dc/elements/1.1/}subject")]
                    formats = [x.text for x in root.findall("{http://purl.org/dc/elements/1.1/}format")]
                    description = root.find("{http://purl.org/dc/elements/1.1/}description")
                    if description == None:
                        print(m)
                    else:
                        outp["description"] = description.text
                    for title in titles:
                        outp["metadata"].append({"label": "Title", "value": title})
                    for creator in creators:
                        outp["metadata"].append({"label": "Creator", "value": creator})
                    for date in dates:
                        outp["metadata"].append({"label": "Date", "value": date})
                    for identifier in identifiers:
                        outp["metadata"].append({"label": "Identifier", "value": identifier})
                    for subject in subjects:
                        outp["metadata"].append({"label": "Subject", "value": subject})
                    for format in formats:
                        outp["metadata"].append({"label": "Format", "value": format})
                    if len(titles) == 4:
                       outp["label"] = titles[2] + " " + titles[0] + ", " + titles[3]
                    elif len(titles) == 3:
                       outp["label"] = titles[2] + " " + titles[0]
                    else:
                        print(title)
                    break
            outp["sequences"] = []
            outp["structures"] = []
            outp["viewingDirection"] = "left-to-right"
            sequence = {}
            sequence_id = uuid4().urn.split(":")[-1]
            sequence_id = manifest_id + "/sequences/" + sequence_id
            sequence["@id"] = sequence_id
            sequence["@type"] = "sc:Sequence"
            sequence["canvases"] = []
            canvas_id = uuid4().urn.split(":")[-1]
            canvas_id = sequence_id + "/canvases/" + canvas_id
            the_img = n
            try:
                img = Image.open(the_img)
                width, height = img.size
            except OSError:
                print("{} could not be opened to get size info".format(the_img))
            except Image.DecompressionBombError:
                print("{} got a DecompressionBombError".format(the_img))
            a_canvas = {}
            a_canvas["@id"] = canvas_id
            a_canvas["@type"] = "sc:Canvas"
            a_canvas["height"] = height
            a_canvas["width"] =  width
            a_canvas["images"] = []

            an_img = {}
            an_img["@context"] = "http://iiif.io/api/presentation/2/context.json"
            img_id = uuid4().urn.split(":")[-1]
            an_img["@id"] = "http://" + img_id
            an_img["@type"] = "oa:Annotation"
            an_img["motivation"] = "sc:Painting"
            an_img["resource"] = {}
            n_path = n.split("/data/voldemort/digital_collections/data/ldr_oc_admin/files/IIIF_Files/")[1]
            n_path = quote(n_path, safe="")
            an_img["resource"]["@id"] = "http://iiif-server.lib.uchicago.edu/" + n_path +  "/full/full/0/default.jpg"
            an_img["resource"]["@type"] = "dctypes:Image"
            an_img["resource"]["format"] = "image/jpeg"
            an_img["resource"]["height"] = height
            an_img["resource"]["width"] = width
            an_img["on"] = canvas_id
            an_img["resource"]["service"] = {}
            an_img["resource"]["service"]["@context"] = "http://iiif.io/api/image/2/context.json"
            an_img["resource"]["service"]["@id"] = "https://iiif-server.lib.uchicago.edu/" + n_path
            img_profile = {}
            img_profile["supports"] = ["canonicalLinkHeader", "profileLinkHeader", "mirroring", "rotationArbitrary", "regionSquare", "sizeAboveFull"]
            img_profile["qualities"] = ["default", "gray", "bitonal"]
            img_profile["format"] = ["jpg", "png", "gif", "webp"]
            an_img["resource"]["service"]["profile"] = ["http://iiif.io/api/image/2/level2.json", img_profile]
            a_canvas["images"].append(an_img)
            sequence["canvases"].append(a_canvas)
            outp["sequences"].append(sequence)
            json_file_name = main_identifier.split(".tif")[0] + ".json"
            json_file_path = join(getcwd(), "manifests", json_file_name)
            json_filepath_dirs = dirname(json_file_path)
            new = "/"
            for n in json_filepath_dirs.split('/'):
                new = join(new, n)
                if not exists(new):
                    mkdir(new)
            with open(json_file_path, "w+", encoding="utf-8") as write_file:
                json.dump(outp, write_file, indent=4)
        return 0
    except KeyboardInterrupt:
        return 131

if __name__ == "__main__":
    _exit(_main())
