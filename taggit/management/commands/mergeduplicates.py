from django.core.management.base import BaseCommand, CommandError
from taggit.models import Tag, TaggedItem
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError

class Command(BaseCommand):
    args = 'none'
    help = '''Reads all tag slugs which end with _1 - _9. Slugifys a lower case version of the name, 
            checks for tag with that slug. If a match, the duplicate is deleted and the objects which 
            referenced it are updated to use the cannonical tag. Useful for cleaning up old messes 
            from case sensitive taggit against lots of content.'''

    def handle(self, *args, **options):
        
        #finds alpha only tag twin twins (up to _9)
        dupe_tags = Tag.objects.filter(slug__regex=r'_\d$')
        count = dupe_tags.count()
        print "Stage 1: De-dupe " + str(count) + " tags."
        #Dedupe the tags which would cause a constraint error on save() with the lowercase name
        for i, tag in enumerate(dupe_tags):
            #destination slug is derived from the new lowercase
            dest_slug = tag.slugify(tag.name.lower())
            print tag.slug + ' -> ' + dest_slug 
            #we join first, then we can delete the twin tag
            self.swap_tag(tag.slug, dest_slug)
            #bye bye
            tag.delete()
        
        #find only tags which contain an uppercase letter
        tags = Tag.objects.filter(name__regex=r'[A-Z]')
        count = tags.count()
        print "Stage 2: Lowercase all " + str(count) + " tags."
        for i, tag in enumerate(tags):
            if Tag.objects.filter(name=tag.name.lower()):
                print 'DUPE: ' + tag.name 
            else:
                tag.name = tag.name.lower()
                tag.save()

        print "Done."
        

    def swap_tag(self, source_slug, dest_slug):
        #Why don't we take all the tags from over here, and put them over there!?!
        try:
            source_tag = Tag.objects.get(slug=source_slug)
        except ObjectDoesNotExist:
            print 'Source Tag does not exist: ' + source_slug
            return
            
        try:
            dest_tag = Tag.objects.get(slug=dest_slug)
        except ObjectDoesNotExist:
            print 'Destination Tag does not exist: ' + dest_slug
            return
        
        items = TaggedItem.objects.filter(tag=source_tag)
        count = items.count()
        for i, item in enumerate(items):
            obj = item.content_object
            if obj:
                #print obj
                obj.tags.remove(source_tag)
                obj.tags.add(dest_tag)
        return   
        