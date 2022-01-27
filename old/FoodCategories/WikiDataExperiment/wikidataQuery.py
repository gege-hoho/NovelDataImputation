import json
import sys
from SPARQLWrapper import SPARQLWrapper, JSON

from preProcessor.categoryReader import Category


def get_results(id):
    endpoint_url = "https://query.wikidata.org/sparql"

    query = """SELECT ?s ?desc ?sitelinks
    WHERE
    {
      ?s wdt:P279 wd:""" + id + """ ;
      wikibase:sitelinks ?sitelinks.
      OPTIONAL {
         ?s rdfs:label ?desc filter (lang(?desc) = "en").
       }
     }
    ORDER BY DESC(?sitelinks)"""

    user_agent = "User-Agent: Food Taxonomy (https://tum.de; gregor.ziegltrum@tum.de)"
    sparql = SPARQLWrapper(endpoint_url, agent=user_agent)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    return sparql.query().convert()


max_depth = 4
def subCategoryCrawler(id, depth=max_depth):
    """
    Crawls the subcategories of an category from wikidata
    :param id:
    :type id:
    :param depth:
    :type depth:
    :return:
    :rtype:
    """
    if depth == 0:
        return {}
    categories = {}
    results = get_results(id)
    for result in results["results"]["bindings"]:
        if "desc" not in result or "value" not in result["desc"]:
            continue
        name = result["desc"]["value"]
        print(name)
        curr_id = result["s"]["value"].lstrip("http://www.wikidata.org/entity/")
        site_links = int(result['sitelinks']['value'])
        # use the number of sitelinks as an importance measure
        if site_links < 40 - ((max_depth-depth)*8):
            break
        sub_cat = subCategoryCrawler(curr_id, depth - 1)

        categories[name] = {
            "name": name,
            "id": curr_id,
            "sub-categories": sub_cat,
            "site-links": site_links
        }


    return categories


w = subCategoryCrawler("Q748611", max_depth) # crawl finger food
x = subCategoryCrawler("Q746549", max_depth) # crawl dishes
y = subCategoryCrawler("Q25403900", max_depth) # crawl food-ingredient
z = subCategoryCrawler("Q2095", max_depth) # crawl food

#combine results
z = {**z, **y, **x, **w}






with open('data/wiki_categories.json', 'w') as fp:
    json.dump(z, fp)
