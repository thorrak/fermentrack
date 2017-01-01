import urllib2
import simplejson as json
import os
from distutils.version import LooseVersion

class gitHubReleases:
    def __init__(self, url):
        """ Gets all available releases using the GitHub API
        :param url: URL to a BrewPi firmware repository on GitHub
        """
        self.url = url
        self.releases = []
        self.update()

    def download(self, url, path):
        """
        Downloads the file at url to destination directory path, saving it with the same filename as in the url.
        :param url: file to download
        :param path: directory to download too.
        :return: full path to file
        """
        try:
            f = urllib2.urlopen(url)
            print "downloading " + url

            # Open our local file for writing
            fileName = os.path.join(path, os.path.basename(url))
            with open(fileName, "wb") as localFile:
                localFile.write(f.read())
            os.chmod(fileName, 0777) # make sure file can be overwritten by a normal user if this ran as root
            return os.path.abspath(fileName)

        #handle errors
        except urllib2.HTTPError, e:
            print "HTTP Error:", e.code, url
        except urllib2.URLError, e:
            print "URL Error:", e.reason, url
        return None

    def update(self):
        """
        Update myself by downloading a list of releases from GitHub
        """
        self.releases = json.load(urllib2.urlopen(self.url + "/releases"))

    def findByTag(self, tag):
        """
        Find release info for release tagged with 'tag'
        :param tag: tag of release
        :return: dictionary with release info. None if not found
        """
        try:
            match = (release for release in self.releases if release["tag_name"] == tag).next()
        except StopIteration:
            print "tag '{0}' not found".format(tag)
            return None
        return match

    def getBinUrl(self, tag, wordsInFileName):
        """
        Finds the download URL for a binary inside a release
        :param tag: tag name of the release
        :param wordsInFileName: words to look for in the filename
        :return: URL to first binary that has all the words in the filename
        """
        release = self.findByTag(tag)
        downloadUrl = None

        AllUrls = (asset["browser_download_url"] for asset in release["assets"])

        for url in  AllUrls:
            urlFileName = url.rpartition('/')[2] # isolate filename, which is after the last /
            if all(word.lower() in urlFileName.lower() for word in wordsInFileName):
                downloadUrl = url
                break
        return downloadUrl

    def getBin(self, tag, wordsInFileName, path=None):
        """
        Writes .bin file in release to target directory
        Defaults to ./downloads/tag_name/ as download location

        :param tag: tag name of the release
        :param wordsInFileName: words to look for in the filename
        :param path: optional target directory
        :return:
        """
        downloadUrl = self.getBinUrl(tag, wordsInFileName)
        if not downloadUrl:
            return None

        if path == None:
            path = os.path.join(os.path.dirname(__file__), "downloads")
            
        downloadDir = os.path.join(os.path.abspath(path), tag)
        if not os.path.exists(downloadDir):
            os.makedirs(downloadDir, 0777) # make sure files can be accessed by all in case the script ran as root

        fileName = self.download(downloadUrl, downloadDir)
        return fileName

    def getLatestTag(self, board, prerelease):
        """
        Get latest tag that contains a binary for the given board
        :param board: board name
        :return: tag of release
        """
        for release in self.releases:
            # search for stable release
            tag = release["tag_name"]
            if self.getBinUrl(tag, [board]):
                if release["prerelease"] == prerelease:
                    return tag
        return None

    def containsSystemImage(self, tag):
        """
        Check wether the release contains a new system image for the Photon
        :param tag: release tag
        :return: True if release contains a system image
        """
        return self.getBinUrl(tag, ['photon', 'system-part1', '.bin']) is not None

    def getLatestTagForSystem(self, prerelease, since = "0.0.0"):
        """
        Query what the latest tag was for which a system image was included
        :param prerelease: True if pre-releases should be included
        :param since: exclude system images older or equal than version included with this version number
        :return: release tag
        """
        for release in self.releases:
            # search for stable release
            tag = release["tag_name"]
            if LooseVersion(tag) <= LooseVersion(since):
                continue
            if not prerelease and release["prerelease"] == True:
                continue
            if self.containsSystemImage(tag):
                return tag
        return None

    def getTags(self, prerelease):
        """
        Get all available tags in repository
        :param prerelease: True if unstable (prerelease) tags should be included
        :return: list of tags
        """
        if prerelease:
            return [release["tag_name"] for release in self.releases]
        else:
            return [release["tag_name"] for release in self.releases if release['prerelease']==False]

if __name__ == "__main__":
    # test code
    releases = gitHubReleases("https://api.github.com/repos/BrewPi/firmware")
    latest = releases.getLatestTag('core', False)
    print "Latest tag: " + latest
    print "Downloading binary for latest tag"
    localFileName = releases.getBin(latest, ["core", "bin"])
    if localFileName:
        print "Latest binary downloaded to " + localFileName

    print "Stable releases: ", releases.getTags(prerelease=False)
    print "All releases: ", releases.getTags(prerelease=True)

    print "Latest stable system image in: ", releases.getLatestTagForSystem(prerelease=False)
    print "Latest beta system image in: ", releases.getLatestTagForSystem(prerelease=True)
