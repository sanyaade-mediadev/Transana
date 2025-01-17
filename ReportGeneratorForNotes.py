# Copyright (C) 2003 - 2015 The Board of Regents of the University of Wisconsin System 
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of version 2 of the GNU General Public License as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#

"""This module implements the Report Generator for NOTES Reports. """

__author__ = 'David K. Woods <dwoods@wcer.wisc.edu>'

# import the Python String module
import string
# import wxPython
import wx
# Import Transana's Clip object
import Clip
# import Transana's Collection Object
import Collection
# Import Transana's Database Interface
import DBInterface
# Import Transana's Dialog Boxes
import Dialogs
# import Transana's Documeng object
import Document
# Import Transana's Episode object
import Episode
# import Transana's Filter Dialog
import FilterDialog
# Import Transana's Note object
import Note
# Import Transana's Quote object
import Quote
# Import Transana's Library Object
import Library
# import Transana's Snapshot Object
import Snapshot
# Import Transana's Text Report infrastructure
import TextReport
# import Transana's Constants
import TransanaConstants
# import Transana's Global variables
import TransanaGlobal
# import Transana's Transcript Object
import Transcript


class ReportGenerator(wx.Object):
    """ This class creates and displays the Object Reports """
    def __init__(self, **kwargs):
        """ Create the Notes Report """
        # Parameters can include:
        # controlObject=None
        # title=''
        # reportType       One of RootNode, LibraryNode, DocumentNode, EpisodeNode, TranscriptNode, CollectionNode, QuoteNode, ClipNode, or SnapshotNode
        # searchText=None  Search Text for Notes Report based on Notes Text Search results

        # Remember the parameters passed in and set values for all variables, even those NOT passed in.
        if kwargs.has_key('controlObject'):
            self.ControlObject = kwargs['controlObject']
        else:
            self.ControlObject = None
        # Specify the Report Title
        if kwargs.has_key('title'):
            self.title = kwargs['title']
        else:
            self.title = ''
        # Specify the Notes Report Type
        if kwargs.has_key('reportType'):
            self.reportType = kwargs['reportType']
        else:
            self.reportType = None
        if kwargs.has_key('searchText'):
            self.searchText = kwargs['searchText']
        else:
            self.searchText = None

        # Filter Configuration Name -- initialize to nothing
        self.configName = ''

        # Create the TextReport object, which forms the basis for text-based reports.
        self.report = TextReport.TextReport(None, title=self.title, displayMethod=self.OnDisplay,
                                            filterMethod=self.OnFilter, helpContext="Transana's Text Reports")
        # If a Control Object has been passed in ...
        if self.ControlObject != None:
            # ... register this report with the Control Object (which adds it to the Windows Menu)
            self.ControlObject.AddReportWindow(self.report)
            # Register the Control Object with the Report
            self.report.ControlObject = self.ControlObject
        # Define the Filter List
        self.filterList = []
        # To speed report creation, freeze GUI updates based on changes to the report text
        self.report.reportText.Freeze()
        # Trigger the ReportText method that causes the report to be displayed.
        self.report.CallDisplay()
        # Apply the Default Filter, if one exists
        self.report.OnFilter(None)
        # Now that we're done, remove the freeze
        self.report.reportText.Thaw()

    def OnDisplay(self, reportText):
        """ This method, required by TextReport, populates the TextReport.  The reportText parameter is
            the wxSTC control from the TextReport object.  It needs to be in the report parent because
            the TextReport doesn't know anything about the actual data.  """
        # Determine if we need to populate the Filter Lists.  If it hasn't already been done, we should do it.
        # If it has already been done, no need to do it again.
        if self.filterList == []:
            populateFilterList = True
        else:
            populateFilterList = False
        # Make the control writable
        reportText.SetReadOnly(False)
        # Set the font for the Report Title
        reportText.SetTxtStyle(fontFace = 'Courier New', fontSize = 16, fontBold = True, fontUnderline = True,
                               parAlign = wx.TEXT_ALIGNMENT_CENTER, parSpacingAfter = 12)
        # Add the Report Title
        reportText.WriteText(self.title)
        # Turn off underlining and bold
        reportText.SetTxtStyle(fontBold = False, fontUnderline = False)
        reportText.Newline()

        if self.searchText != None:
            # ...  add a subtitle
            if 'unicode' in wx.PlatformInfo:
                # Encode with UTF-8 rather than TransanaGlobal.encoding because this is a prompt, not DB Data.
                prompt = unicode(_("Search Text: %s"), 'utf8')
            else:
                prompt = _("Search Text: %s")
            self.subtitle = prompt % self.searchText
            # ... set the font for the subtitle ...
            reportText.SetTxtStyle(fontSize = 10)
            # ... and insert the spacer and the subtitle.
            reportText.WriteText(self.subtitle)
            reportText.Newline()

        if self.configName != '':
            # ...  add a subtitle
            if 'unicode' in wx.PlatformInfo:
                # Encode with UTF-8 rather than TransanaGlobal.encoding because this is a prompt, not DB Data.
                prompt = unicode(_("Filter Configuration: %s"), 'utf8')
            else:
                prompt = _("Filter Configuration: %s")
            self.configLine = prompt % self.configName
            # ... set the font for the subtitle ...
            reportText.SetTxtStyle(fontSize = 10)
            # ... and insert the subtitle.
            reportText.WriteText(self.configLine)
            reportText.Newline()

        # If a Root Node flag is passed in ...
        if self.reportType == 'RootNode':
            # ... we want to group notes by category.  (They will be alphabetical within each category.)
            majorList = DBInterface.list_of_all_notes(reportType='LibraryNode', searchText=self.searchText)
            if TransanaConstants.proVersion:
                majorList += DBInterface.list_of_all_notes(reportType='DocumentNode', searchText=self.searchText)
            majorList += DBInterface.list_of_all_notes(reportType='EpisodeNode', searchText=self.searchText)
            majorList += DBInterface.list_of_all_notes(reportType='TranscriptNode', searchText=self.searchText)
            majorList += DBInterface.list_of_all_notes(reportType='CollectionNode', searchText=self.searchText)
            if TransanaConstants.proVersion:
                majorList += DBInterface.list_of_all_notes(reportType='QuoteNode', searchText=self.searchText)
            majorList += DBInterface.list_of_all_notes(reportType='ClipNode', searchText=self.searchText)
            if TransanaConstants.proVersion:
                majorList += DBInterface.list_of_all_notes(reportType='SnapshotNode', searchText=self.searchText)
        # if a specific Node flag is passed in ...
        else:
            # ... and use the Notes from the requested Report Type for the majorList. 
            majorList = DBInterface.list_of_all_notes(reportType=self.reportType, searchText=self.searchText)

        # Initialize the initial data structure that will be turned into the report
        self.data = []
        # We need a list of all checked NoteNums to apply the Filter.  Initialize it here.
        checkedRecords = []
        # Now populate it based on the Filter List.  (The filterList will be empty if not populate yet, but that's OK.)
        # Iterate through the filter list ...
        for noteRecord in self.filterList:
            # ... pull out the filter list record elements.
            (noteNum, noteID, noteParent, checked) = noteRecord
            # If an item is checked ...
            if checked:
                # ... add it to the list of checked items!
                checkedRecords.append(noteNum)

        # Iterate through the major list
        for noteRecord in majorList:
            # If the current item from the Major List is in the list of checked records from the filter dialog
            # OR if we're going through the list for the first time (populateFilterList == True) ....
            if (noteRecord['NoteNum'] in checkedRecords) or populateFilterList:
                # ... load each note ...
                tempNote = Note.Note(noteRecord['NoteNum'])
                # Turn bold on.
                reportText.SetTxtStyle(fontBold = True, fontSize = 12,
                                       parAlign = wx.TEXT_ALIGNMENT_LEFT, parLeftIndent = 0,
                                       parSpacingBefore = 36, parSpacingAfter = 12)
                # Add the note ID to the report
                reportText.WriteText('%s' % tempNote.id)
                reportText.Newline()

                # Initialize all temporary objects to None so we can detect their presence or absence
                tempLibrary = None
                tempDocument = None
                tempEpisode = None
                tempTranscript = None
                tempCollection = None
                tempQuote = None
                tempClip = None
                tempSnapshot = None
                # If we have a Library Note ...
                if tempNote.series_num > 0:
                    # ... load the Library data
                    tempLibrary = Library.Library(tempNote.series_num)
                    noteParent = unicode(_('Libraries'), 'utf8') + ' ' + tempLibrary.id
                # If we have a Document Note ...
                elif tempNote.document_num > 0:
                    # ... load the Document and Library data
                    tempDocument = Document.Document(tempNote.document_num)
                    tempLibrary = Library.Library(tempDocument.library_num)
                    noteParent = unicode(_('Document'), 'utf8') + ' ' + tempLibrary.id + ' > ' + tempDocument.id
                # If we have an Episode Note ...
                elif tempNote.episode_num > 0:
                    # ... load the Episode and Library data
                    tempEpisode = Episode.Episode(tempNote.episode_num)
                    tempLibrary = Library.Library(tempEpisode.series_num)
                    noteParent = unicode(_('Episode'), 'utf8') + ' ' + tempLibrary.id + ' > ' + tempEpisode.id
                # If we have a Transcript Note ...
                elif tempNote.transcript_num > 0:
                    # ... load the Transcript, Episode, and Library data
                    # To save time here, we can skip loading the actual transcript text, which can take time once we start dealing with images!
                    tempTranscript = Transcript.Transcript(tempNote.transcript_num, skipText=True)
                    tempEpisode = Episode.Episode(tempTranscript.episode_num)
                    tempLibrary = Library.Library(tempEpisode.series_num)
                    noteParent = unicode(_('Transcript'), 'utf8') + ' ' + tempLibrary.id + ' > ' + tempEpisode.id + ' > ' + tempTranscript.id
                # If we have a Collection Note ...
                elif tempNote.collection_num > 0:
                    # ... load the Collection data
                    tempCollection = Collection.Collection(tempNote.collection_num)
                    noteParent = unicode(_('Collection'), 'utf8') + ' ' + tempCollection.GetNodeString()
                # If we have a Quote Note ...
                elif tempNote.quote_num > 0:
                    # ... load the Quote and Collection data.  We can skip loading the Quote text to save load time
                    tempQuote = Quote.Quote(tempNote.quote_num, skipText=True)
                    tempCollection = Collection.Collection(tempQuote.collection_num)
                    noteParent = unicode(_('Quote'), 'utf8') + ' ' + tempCollection.GetNodeString() + ' > ' + tempQuote.id
                # If we have a Clip Note ...
                elif tempNote.clip_num > 0:
                    # ... load the Clip and Collection data.  We can skip loading the Clip Transcript to save load time
                    tempClip = Clip.Clip(tempNote.clip_num, skipText=True)
                    tempCollection = Collection.Collection(tempClip.collection_num)
                    noteParent = unicode(_('Clip'), 'utf8') + ' ' + tempCollection.GetNodeString() + ' > ' + tempClip.id
                # If we have a Snapshot Note ...
                elif tempNote.snapshot_num > 0:
                    # ... load the Snapshot and Collection data.
                    tempSnapshot = Snapshot.Snapshot(tempNote.snapshot_num)
                    tempCollection = Collection.Collection(tempSnapshot.collection_num)
                    noteParent = unicode(_('Snapshot'), 'utf8') + ' ' + tempCollection.GetNodeString() + ' > ' + tempSnapshot.id

                # If we have Library data ...
                if tempLibrary != None:
                    # Turn bold on.
                    reportText.SetTxtStyle(fontSize = 10, fontBold = True, parLeftIndent = 63, parSpacingBefore = 0, parSpacingAfter = 0)
                    # Add the note ID to the report
                    reportText.WriteText(_('Library: '))
                    # Turn bold off.
                    reportText.SetTxtStyle(fontBold = False)
                    # Add the Library ID
                    reportText.WriteText('%s' % tempLibrary.id)
                    reportText.Newline()
                # If we have Document data ...
                if tempDocument != None:
                    # Turn bold on.
                    reportText.SetTxtStyle(fontBold = True)
                    # Add the note ID to the report
                    reportText.WriteText(_('Document: '))
                    # Turn bold off.
                    reportText.SetTxtStyle(fontBold = False)
                    # Add the Document ID
                    reportText.WriteText('%s' % tempDocument.id)
                    reportText.Newline()
                # If we have Episode data ...
                if tempEpisode != None:
                    # Turn bold on.
                    reportText.SetTxtStyle(fontBold = True)
                    # Add the note ID to the report
                    reportText.WriteText(_('Episode: '))
                    # Turn bold off.
                    reportText.SetTxtStyle(fontBold = False)
                    # Add the Episode ID
                    reportText.WriteText('%s' % tempEpisode.id)
                    reportText.Newline()
                # If we have Transcript data ...
                if tempTranscript != None:
                    # Turn bold on.
                    reportText.SetTxtStyle(fontBold = True)
                    # Add the note ID to the report
                    reportText.WriteText(_('Transcript: '))
                    # Turn bold off.
                    reportText.SetTxtStyle(fontBold = False)
                    # Add the Transcript ID
                    reportText.WriteText('%s' % tempTranscript.id)
                    reportText.Newline()
                # If we have Collection data ...
                if tempCollection != None:
                    # Turn bold on.
                    reportText.SetTxtStyle(fontSize = 10, fontBold = True, parLeftIndent = 63, parSpacingBefore = 0, parSpacingAfter = 0)
                    # Add the note ID to the report
                    reportText.WriteText(_('Collection: '))
                    # Turn bold off.
                    reportText.SetTxtStyle(fontBold = False)
                    # Add the Collection ID
                    reportText.WriteText('%s' % tempCollection.GetNodeString())
                    reportText.Newline()
                # If we have Quote data ...
                if tempQuote != None:
                    # Turn bold on.
                    reportText.SetTxtStyle(fontBold = True)
                    # Add the note ID to the report
                    reportText.WriteText(_('Quote: '))
                    # Turn bold off.
                    reportText.SetTxtStyle(fontBold = False)
                    # Add the Quote ID
                    reportText.WriteText('%s' % tempQuote.id)
                    reportText.Newline()
                # If we have Clip data ...
                if tempClip != None:
                    # Turn bold on.
                    reportText.SetTxtStyle(fontBold = True)
                    # Add the note ID to the report
                    reportText.WriteText(_('Clip: '))
                    # Turn bold off.
                    reportText.SetTxtStyle(fontBold = False)
                    # Add the Clip ID
                    reportText.WriteText('%s' % tempClip.id)
                    reportText.Newline()
                # If we have Snapshot data ...
                if tempSnapshot != None:
                    # Turn bold on.
                    reportText.SetTxtStyle(fontBold = True)
                    # Add the note ID to the report
                    reportText.WriteText(_('Snapshot: '))
                    # Turn bold off.
                    reportText.SetTxtStyle(fontBold = False)
                    # Add the Snapshot ID
                    reportText.WriteText('%s' % tempSnapshot.id)
                    reportText.Newline()

                # If we're going through the list for the first time and need to populate the filter list ...
                if populateFilterList:
                    # ... add the note number, note ID, note parent info, and checked=True to the filter list.
                    self.filterList.append((tempNote.number, tempNote.id, noteParent, True))

                # Turn bold on.
                reportText.SetTxtStyle(fontBold = True)
                # Add the note ID to the report
                reportText.WriteText(_('Note Taker: '))
                # Turn bold off.
                reportText.SetTxtStyle(fontBold = False)
                # Add the Note's author
                reportText.WriteText('%s' % tempNote.author)
                reportText.Newline()
                # Turn bold on.
                reportText.SetTxtStyle(fontBold = True)
                # Add the note ID to the report
                reportText.WriteText(_('Note Text:'))
                reportText.Newline()
                # Turn bold off.
                reportText.SetTxtStyle(fontBold = False, parLeftIndent = 127)
                # Add the note text to the report (rstrip() prevents formatting problems when notes end with blank lines)
                reportText.WriteText('%s' % tempNote.text.rstrip())
                reportText.Newline()

            
        # Make the control read only, now that it's done
        reportText.SetReadOnly(True)


    def OnFilter(self, event):
        """ This method, required by TextReport, implements the call to the Filter Dialog.  It needs to be
            in the report parent because the TextReport doesn't know the appropriate filter parameters. """
        # See if we're loading the Default profile.  This is signalled by an event of None!
        if event == None:
            loadDefault = True
        else:
            loadDefault = False
        # Determine the Report Scope
        if self.reportType == 'RootNode':
            reportScope = 1
        elif self.reportType == 'LibraryNode':
            reportScope = 2
        elif self.reportType == 'EpisodeNode':
            reportScope = 3
        elif self.reportType == 'TranscriptNode':
            reportScope = 4
        elif self.reportType == 'CollectionNode':
            reportScope = 5
        elif self.reportType == 'ClipNode':
            reportScope = 6
        elif self.reportType == 'SnapshotNode':
            reportScope = 7
        elif self.reportType == 'DocumentNode':
            reportScope = 8
        elif self.reportType == 'QuoteNode':
            reportScope = 9
        # Define the Filter Dialog.  We need reportType 13 to identify the Notes Report, the appropriate reportScope,
        # and the capacity to filter Notes.
        dlgFilter = FilterDialog.FilterDialog(self.report, -1, self.title, reportType=13,
                                              reportScope=reportScope, loadDefault=loadDefault, configName=self.configName,
                                              notesFilter=True)
        # Populate the Filter Dialog with the Notes Filter list
        dlgFilter.SetNotes(self.filterList)
        # If we're loading the Default configuration ...
        if loadDefault:
            # ... get the list of existing configuration names.
            profileList = dlgFilter.GetConfigNames()
            # If (translated) "Default" is in the list ...
            # (NOTE that the default config name is stored in English, but gets translated by GetConfigNames!)
            if unicode(_('Default'), 'utf8') in profileList:
                # ... then signal that we need to load the config.
                dlgFilter.OnFileOpen(None)
                # Fake that we asked the user for a filter name and got an OK
                result = wx.ID_OK
            # If we're loading a Default profile, but there's none in the list, we can skip
            # the rest of the Filter method by pretending we got a Cancel from the user.
            else:
                result = wx.ID_CANCEL
        # If we're not loading a Default profile ...
        else:
            # ... we need to show the Filter Dialog here.
            result = dlgFilter.ShowModal()
            
        # If the user clicks OK (or we have a Default config)
        if result == wx.ID_OK:
            # ... get the filter data ...
            self.filterList = dlgFilter.GetNotes()
            # Remember the configuration name for later reuse
            self.configName = dlgFilter.configName
            # ... and signal the TextReport that the filter is to be applied.
            return True
        # If the filter is cancelled by the user ...
        else:
            # ... signal the TextReport that the filter is NOT to be applied.
            return False
