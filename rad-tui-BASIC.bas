'' ==========================================================
'' VB1-DOS Clone: Custom Painting & Live Keyboard Editing
'' ==========================================================
#include "fbgfx.bi"

Namespace tui

    '' --------------------------------------------------------
    '' WIDGET/CONTROL DATA TYPE
    '' --------------------------------------------------------
    Type uicontrol
        x As Integer
        y As Integer
        w As Integer          '' Width for resizing
        h As Integer          '' Height
        tool_type As Integer  
        name_id As String     '' The internal variable name (e.g., "Command1")
        caption As String     '' The display text (e.g., "7" or "0.")
    End Type

    '' --------------------------------------------------------
    '' WINDOW CLASS 
    '' --------------------------------------------------------
    Type window
        Declare Constructor(new_x As Integer = 1, new_y As Integer = 1, new_w As Integer = 20, new_h As Integer = 5, new_title As String = "")
        Declare Destructor()
        Declare Sub show()
        Declare Sub add_control(cx As Integer, cy As Integer, ctype As Integer, ctitle As String)

        '' Public Properties
        Declare Property title As String
        Declare Property title(new_title As String)
        Declare Property x As Integer
        Declare Property x(new_x As Integer)
        Declare Property y As Integer
        Declare Property y(new_y As Integer)
        
        Declare Property w As Integer
        Declare Property h As Integer
        Declare Property count As Integer
        
        Declare Function HitTest(mx As Integer, my As Integer) As Boolean
        Declare Function HitControl(lx As Integer, ly As Integer) As Integer
        Declare Function get_control(idx As Integer) As uicontrol Ptr

    Private:
        Declare Sub redraw()
        Declare Sub remove()
        Declare Sub drawtitle()

        Dim As String mytitle
        Dim As Integer posx, posy, sizew, sizeh
        
        Dim As uicontrol controls(1 To 20)
        Dim As Integer control_count
    End Type

    Constructor window(new_x As Integer, new_y As Integer, new_w As Integer, new_h As Integer, new_title As String)
        This.posx = new_x
        This.posy = new_y
        This.sizew = new_w
        This.sizeh = new_h
        This.mytitle = new_title
        This.control_count = 0
        If(Len(This.mytitle) = 0) Then This.mytitle = "untitled"
    End Constructor

    Destructor window()
    End Destructor

    Sub window.add_control(cx As Integer, cy As Integer, ctype As Integer, ctitle As String)
        If This.control_count < 20 Then
            This.control_count += 1
            This.controls(This.control_count).x = cx
            This.controls(This.control_count).y = cy
            This.controls(This.control_count).tool_type = ctype
            
            '' Set default sizes and properties based on tool type
            This.controls(This.control_count).name_id = "ctrl" & This.control_count
            
            If ctype = 3 Then '' Command Button
                This.controls(This.control_count).w = 9
                This.controls(This.control_count).h = 1
                This.controls(This.control_count).caption = "Button"
            ElseIf ctype = 13 Then '' Text Box
                This.controls(This.control_count).w = 15
                This.controls(This.control_count).h = 1
                This.controls(This.control_count).caption = "Text1"
            Else
                '' Default for other controls
                This.controls(This.control_count).w = 12
                This.controls(This.control_count).h = 1
                This.controls(This.control_count).caption = Trim(ctitle)
            End If
            
            This.redraw()
        End If
    End Sub

    Property window.title() As String
        Return This.mytitle
    End Property

    Property window.title(new_title As String)
        This.mytitle = new_title
        This.drawtitle()
    End Property

    Property window.x() As Integer
        Return This.posx
    End Property

    Property window.x(new_x As Integer)
        This.remove()
        If new_x < 1 Then new_x = 1
        If new_x + This.sizew - 1 > 80 Then new_x = 80 - This.sizew + 1
        This.posx = new_x
        This.redraw()
    End Property

    Property window.y() As Integer
        Return This.posy
    End Property

    Property window.y(new_y As Integer)
        This.remove()
        If new_y < 2 Then new_y = 2
        If new_y + This.sizeh - 1 > 25 Then new_y = 25 - This.sizeh + 1
        This.posy = new_y
        This.redraw()
    End Property

    Property window.w() As Integer
        Return This.sizew
    End Property

    Property window.h() As Integer
        Return This.sizeh
    End Property
    
    Property window.count() As Integer
        Return This.control_count
    End Property

    Function window.get_control(idx As Integer) As uicontrol Ptr
        If idx > 0 And idx <= This.control_count Then Return @This.controls(idx)
        Return 0
    End Function

    Sub window.show()
        This.redraw()
    End Sub

    Sub window.drawtitle()
        Locate This.posy, This.posx
        Color 15, 1 
        Print Space(This.sizew);
        Locate This.posy, This.posx + (This.sizew \ 2) - (Len(This.mytitle) \ 2)
        Print This.mytitle;
    End Sub

    Sub window.remove()
        Color 7, 0 
        Var spaces = Space(This.sizew)
        For i As Integer = This.posy To This.posy + This.sizeh - 1
            Locate i, This.posx
            Print spaces;
        Next
    End Sub

    Sub window.redraw()
        This.drawtitle()
        
        '' Draw Window Background (Dark Grey on Light Grey)
        Color 8, 7 
        Var spaces = Space(This.sizew)
        For i As Integer = This.posy + 1 To This.posy + This.sizeh - 1
            Locate i, This.posx
            Print spaces;
        Next
        
        '' Custom Paint Event for Child Controls
        For i As Integer = 1 To This.control_count
            Dim As Integer draw_y = This.posy + This.controls(i).y
            Dim As Integer draw_x = This.posx + This.controls(i).x
            Dim As String cap = This.controls(i).caption
            Dim As Integer wid = This.controls(i).w
            
            If This.controls(i).tool_type = 3 Then
                '' COMMAND BUTTON: [ Caption ] styling
                Color 0, 7 '' Black text on Grey
                '' Center the caption inside the button brackets
                Dim As String btn_text = Space((wid - 2 - Len(cap)) \ 2) & cap & Space((wid - 2 - Len(cap)) \ 2)
                '' Pad any remainder to ensure exact width
                btn_text = Left(btn_text & Space(wid), wid - 2)
                
                Locate draw_y, draw_x
                Print "[" & btn_text & "]";
                
            ElseIf This.controls(i).tool_type = 13 Then
                '' TEXT BOX: Cyan background, white text (like your screenshot)
                Color 15, 3 
                '' Right-align the text (common for calculators)
                Dim As String txt_text = Space(wid - Len(cap) - 2) & cap
                txt_text = Right(Space(wid) & txt_text, wid - 2)
                
                Locate draw_y, draw_x
                Print "[" & txt_text & "]";
                
            Else
                '' GENERIC FALLBACK
                Color 0, 3 
                Locate draw_y, draw_x
                Print "[" & Left(cap & Space(wid), wid - 2) & "]";
            End If
        Next
    End Sub
    
    Function window.HitTest(mx As Integer, my As Integer) As Boolean
        If mx >= This.posx And mx < This.posx + This.sizew Then
            If my >= This.posy And my < This.posy + This.sizeh Then
                Return True
            End If
        End If
        Return False
    End Function
    
    '' Check if a local coordinate clicks directly on an existing widget
    Function window.HitControl(lx As Integer, ly As Integer) As Integer
        '' Iterate backwards to select the top-most control if overlapping
        For i As Integer = This.control_count To 1 Step -1
            '' --- FIXED ERROR 18: Use explicit width (.w) instead of string length ---
            Dim As Integer c_len = This.controls(i).w
            If ly = This.controls(i).y Then
                If lx >= This.controls(i).x And lx < This.controls(i).x + c_len Then
                    Return i
                End If
            End If
        Next
        Return 0
    End Function

    '' --------------------------------------------------------
    '' TOOLBOX CLASS 
    '' --------------------------------------------------------
    Type Toolbox
        x As Integer
        y As Integer
        w As Integer
        h As Integer
        items(0 To 15) As String
        active_tool As Integer 
        
        Declare Constructor(px As Integer, py As Integer)
        Declare Sub draw()
        Declare Function process_click(mx As Integer, my As Integer) As Boolean
    End Type

    Constructor Toolbox(px As Integer, py As Integer)
        This.x = px
        This.y = py
        This.w = 16 
        This.h = 20
        This.active_tool = 0 
        
        This.items(0) = "Move/Size"
        This.items(1) = "Check Box"
        This.items(2) = "Combo Box"
        This.items(3) = "Command Btn"
        This.items(4) = "Dir List"
        This.items(5) = "Drive List"
        This.items(6) = "File List"
        This.items(7) = "Frame"
        This.items(8) = "HScrollBar"
        This.items(9) = "Label"
        This.items(10) = "List Box"
        This.items(11) = "Option Btn"
        This.items(12) = "Picture Box"
        This.items(13) = "Text Box"
        This.items(14) = "Timer"
        This.items(15) = "VScrollBar"
    End Constructor

    Sub Toolbox.draw()
        Color 0, 3 
        
        Locate This.y, This.x
        Print Chr(218); String(This.w - 2, 196); Chr(191);
        Locate This.y, This.x + (This.w \ 2) - 3
        Print "-Tools-";
        
        Dim As Integer current_y = This.y + 1
        
        Locate current_y, This.x
        Print Chr(179);
        If This.active_tool = 0 Then Color 3, 0 Else Color 0, 3
        Print Left(This.items(0) & Space(This.w - 2), This.w - 2);
        Color 0, 3
        Print Chr(179);
        current_y += 1
        
        Locate current_y, This.x
        Print Chr(195); String(This.w - 2, 196); Chr(180);
        current_y += 1
        
        For i As Integer = 1 To 15
            Locate current_y, This.x
            Print Chr(179); 
            If This.active_tool = i Then Color 3, 0 Else Color 0, 3
            Print Left(This.items(i) & Space(This.w - 2), This.w - 2); 
            Color 0, 3
            Print Chr(179);
            current_y += 1
        Next
        
        Locate current_y, This.x
        Print Chr(192); String(This.w - 2, 196); Chr(217);
    End Sub

    Function Toolbox.process_click(mx As Integer, my As Integer) As Boolean
        If mx >= This.x And mx < This.x + This.w Then
            If my = This.y + 1 Then 
                This.active_tool = 0
                Return True
            ElseIf my >= This.y + 3 And my <= This.y + 17 Then
                This.active_tool = my - (This.y + 2)
                Return True
            End If
        End If
        Return False
    End Function

End Namespace

'' ==========================================================
'' MAIN EXECUTION 
'' ==========================================================

Width 80, 25
Color 7, 0
Cls

Dim As tui.Toolbox tools = tui.Toolbox(2, 3)

Dim As tui.window Ptr windows(1 To 2)
windows(1) = New tui.window(22, 5, 36, 12, "Form 1")
windows(2) = New tui.window(60, 3, 20, 15, "Properties")

'' Initialize Selection State for the Properties Window
Dim As Integer selected_win_idx = 0
Dim As Integer selected_ctrl_idx = 0

Color 0, 7
Locate 1, 1: Print " File  Edit  View  Run  Debug  Options"; Space(40);
tools.draw()
For i As Integer = 1 To 2
    windows(i)->show()
Next

Dim As Integer mx = 0, my = 0, mwheel = 0, mbuttons = 0
Dim As Integer old_mx = 0, old_my = 0
Dim As Integer dragged_win = 0, drag_offset_x = 0, drag_offset_y = 0 
Dim As Boolean was_clicked = False
Dim As Boolean redraw_properties = True 
Dim As String key_press

'' Terminal mapping
Dim As Integer MOUSE_OFFSET_X = 1
Dim As Integer MOUSE_OFFSET_Y = 1 

While 1
    key_press = Inkey()
    If key_press = Chr(27) Then Exit While '' Escape quits the program
    
    '' ----------------------------------------------------
    '' NEW: Keyboard Live Editing for Widget Captions
    '' ----------------------------------------------------
    If key_press <> "" And selected_win_idx > 0 And selected_ctrl_idx > 0 Then
        Dim As tui.uicontrol Ptr c = windows(selected_win_idx)->get_control(selected_ctrl_idx)
        If c <> 0 Then
            If key_press = Chr(8) Then '' Backspace pressed
                If Len(c->caption) > 0 Then c->caption = Left(c->caption, Len(c->caption) - 1)
            ElseIf Len(key_press) = 1 And Asc(key_press) >= 32 And Asc(key_press) <= 126 Then
                c->caption &= key_press '' Append typed character
            End If
            
            '' Force a redraw so you can see your typing
            windows(selected_win_idx)->show()
            redraw_properties = True
        End If
    End If

    '' ----------------------------------------------------
    '' Mouse Polling
    '' ----------------------------------------------------
    GetMouse mx, my, mwheel, mbuttons
    
    If mx <> -1 Then
        mx += MOUSE_OFFSET_X
        my += MOUSE_OFFSET_Y
        
        Dim As Boolean mouse_moved = (mx <> old_mx Or my <> old_my)
        Dim As Boolean left_click = (mbuttons And 1) <> 0
        
        If left_click Then
            If was_clicked = False Then
                was_clicked = True
                
                If my = 1 Then
                    Color 15, 0: Locate 1, 60: Print "Menu Clicked!       ": Color 0, 7
                    
                ElseIf tools.process_click(mx, my) Then
                    tools.draw() 
                    Color 15, 0: Locate 1, 60: Print "Selected: " & Trim(tools.items(tools.active_tool)) & Space(10): Color 0, 7
                    
                Else
                    For i As Integer = 2 To 1 Step -1
                        If windows(i)->HitTest(mx, my) Then
                            
                            Dim As Integer local_x = mx - windows(i)->x
                            Dim As Integer local_y = my - windows(i)->y
                                
                            If tools.active_tool = 0 Then
                                '' Check if user clicked directly on a placed widget
                                Dim As Integer clicked_ctrl = windows(i)->HitControl(local_x, local_y)
                                
                                If clicked_ctrl > 0 Then
                                    '' Widget Selected
                                    selected_win_idx = i
                                    selected_ctrl_idx = clicked_ctrl
                                    redraw_properties = True
                                Else
                                    '' Background clicked - Drag Window
                                    dragged_win = i
                                    drag_offset_x = mx - windows(i)->x
                                    drag_offset_y = my - windows(i)->y
                                End If
                                
                            Else
                                '' Place a new Widget
                                If local_x > 0 And local_x < windows(i)->w - 14 And local_y > 0 And local_y < windows(i)->h - 1 Then
                                    windows(i)->add_control(local_x, local_y, tools.active_tool, tools.items(tools.active_tool))
                                    
                                    '' Auto-select the newly placed widget
                                    selected_win_idx = i
                                    selected_ctrl_idx = windows(i)->count
                                    redraw_properties = True
                                    
                                    tools.active_tool = 0 
                                    tools.draw()
                                End If
                            End If
                            Exit For
                        End If
                    Next
                End If
            End If
            
            '' Handle Window Dragging
            If dragged_win > 0 And mouse_moved Then
                windows(dragged_win)->x = mx - drag_offset_x
                windows(dragged_win)->y = my - drag_offset_y
                
                tools.draw()
                For i As Integer = 1 To 2
                    If i <> dragged_win Then windows(i)->show()
                Next
                windows(dragged_win)->show()
                redraw_properties = True
            End If
            
        Else
            was_clicked = False
            dragged_win = 0 
        End If

        '' ----------------------------------------------------
        '' Render Active Properties inside Windows(2)
        '' ----------------------------------------------------
        If redraw_properties Then
            Dim As tui.window Ptr prop_win = windows(2)
            Color 0, 7
            
            If selected_win_idx > 0 And selected_ctrl_idx > 0 Then
                Dim As tui.uicontrol Ptr c = windows(selected_win_idx)->get_control(selected_ctrl_idx)
                If c <> 0 Then
                    '' --- FIXED ERROR 9: Read from tools array instead of c->title, added caption and name ---
                    Locate prop_win->y + 2, prop_win->x + 2: Print Left("Type: " & Trim(tools.items(c->tool_type)) & Space(17), 17);
                    Locate prop_win->y + 4, prop_win->x + 2: Print Left("Name: " & c->name_id & Space(17), 17);
                    Locate prop_win->y + 5, prop_win->x + 2: Print Left("Cap:  " & Left(c->caption, 11) & Space(17), 17);
                    Locate prop_win->y + 7, prop_win->x + 2: Print Left("X:" & c->x & " Y:" & c->y & " W:" & c->w & Space(17), 17);
                End If
            Else
                Locate prop_win->y + 2, prop_win->x + 2: Print Left("No selection." & Space(17), 17);
                Locate prop_win->y + 4, prop_win->x + 2: Print Space(17);
                Locate prop_win->y + 5, prop_win->x + 2: Print Space(17);
                Locate prop_win->y + 7, prop_win->x + 2: Print Space(17);
            End If
            redraw_properties = False
        End If

        If mouse_moved Then
            old_mx = mx
            old_my = my
        End If
        
        '' ----------------------------------------------------
        '' Hardware Blinking Cursor Mapping
        '' ----------------------------------------------------
        If mx >= 1 And mx <= 80 And my >= 1 And my <= 25 Then
            Locate my, mx, 1 
        End If
    End If
    
    Sleep 10, 1 
Wend

For i As Integer = 1 To 2
    Delete windows(i)
Next
Color 7, 0
Cls