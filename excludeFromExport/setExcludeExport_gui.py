
import wpf, clr, sys, os

clr.AddReference("System.Windows.Forms")

import System
from System.Windows import HorizontalAlignment, MessageBox, MessageBoxButton, MessageBoxImage
from System.Windows.Controls import StackPanel, Button, Label, TextBox, ComboBox

# ------------------------------------- #
# -------------- GUI Code ------------- #
# ------------------------------------- #

GUI_XAML_FILE = os.path.join( os.path.split(os.path.realpath(__file__))[0], "setExcludeExport_gui.xaml")
DEFAULT_TITLE = 'CHECK SELECTION FOR EXPORT!'
DEFAULT_PROMPT = 'Are you happy with the ROIs to be exported?'

USER_HAPPY = None

class CheckerDialog(System.Windows.Window):

  # ------------------ #  
  #def getValue(self):
  #  return 0
  # ------------------ #
  
  def __init__(self, prompt=DEFAULT_PROMPT, title=DEFAULT_TITLE):
    """    
    Warning to check ROIs selected for export
    Ok and cancel buttons
    """
    
    wpf.LoadComponent(self, GUI_XAML_FILE)
    
    self.Title = title
    self.lblPrompt.Content = prompt
  
  # ------------------ #
  
  
  
  # Eventhandler
  def ok_clicked(self, sender, event):
    """
    Close dialog
    """
    """
    try:
      self.num_value = float(self.numValBox.Text)
    except:
      MessageBox.Show("Invalid value entered.", "Problem", MessageBoxButton.OK, MessageBoxImage.Information)
      return
    """
      
    #USER_HAPPY = 1   
    self.Close()
  
  # ------------------ #
  
  '''
  def cancel_clicked(self, sender, event):
    """
    Close dialog
    """
    #self.num_value = None
    
    #USER_HAPPY = 0
    self.Close()
  '''
# ------------------------------------------- #



def generateWarning(prompt=DEFAULT_PROMPT, title=DEFAULT_TITLE):
  """
    create window i.e. CheckerDialog object
  """
  dialog = CheckerDialog(prompt=prompt, title=title)
  dialog.ShowDialog()
  
  #return USER_HAPPY
  
  
# ------------------------------------------- #
 

 
def test():
  generateWarning()
  
# ------------------------------------------- #
  
  
  
if __name__ == '__main__':
  test()
