import React, { createContext, useContext, useState, useCallback } from 'react';
import { DndProvider } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';

const DragDropContext = createContext();

export const useDragDrop = () => {
  const context = useContext(DragDropContext);
  if (!context) {
    throw new Error('useDragDrop must be used within a DragDropProvider');
  }
  return context;
};

export const DragDropProvider = ({ children }) => {
  const [draggedItem, setDraggedItem] = useState(null);
  const [dragOverItem, setDragOverItem] = useState(null);
  const [dropZones, setDropZones] = useState(new Map());

  const registerDropZone = useCallback((id, element, onDrop) => {
    setDropZones(prev => new Map(prev.set(id, { element, onDrop })));
    return () => {
      setDropZones(prev => {
        const newZones = new Map(prev);
        newZones.delete(id);
        return newZones;
      });
    };
  }, []);

  const handleDragStart = useCallback((item) => {
    setDraggedItem(item);
  }, []);

  const handleDragEnd = useCallback(() => {
    setDraggedItem(null);
    setDragOverItem(null);
  }, []);

  const handleDragOver = useCallback((zoneId, item) => {
    setDragOverItem({ zoneId, item });
  }, []);

  const handleDrop = useCallback((zoneId, item) => {
    const dropZone = dropZones.get(zoneId);
    if (dropZone && dropZone.onDrop) {
      dropZone.onDrop(item);
    }
    setDraggedItem(null);
    setDragOverItem(null);
  }, [dropZones]);

  const value = {
    draggedItem,
    dragOverItem,
    registerDropZone,
    handleDragStart,
    handleDragEnd,
    handleDragOver,
    handleDrop
  };

  return (
    <DragDropContext.Provider value={value}>
      <DndProvider backend={HTML5Backend}>
        {children}
      </DndProvider>
    </DragDropContext.Provider>
  );
};